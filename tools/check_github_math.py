"""Compare the seven chapters' TeX with what GitHub hands to MathJax.

After pushing, run: python tools/check_github_math.py <commit SHA or branch>
Use the same checkout as the target ref. This checks GitHub's HTML; open the
preview in a browser as well to catch render errors such as rejected macros.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
from difflib import SequenceMatcher
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
REPO = "https://github.com/EXCILLEX-Marisa/volterra-wiki"
BUNDLE = "Volterra_Wiki_00-06_完整合订版_GitHub图床.md"
MATH = re.compile(
    r"^(?P<prefix>[ \t]*(?:> )?)```math[ \t]*\n"
    r"(?P<block>.*?)^(?P=prefix)```[ \t]*$"
    r"|\$`(?P<inline>[^`\n]+)`\$",
    re.MULTILINE | re.DOTALL,
)


class Preview(HTMLParser):
    def __init__(self):
        super().__init__()
        self.article = False
        self.in_article = False
        self.current = None
        self.formulas = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = attrs.get("class", "").split()
        if tag == "article" and "markdown-body" in classes:
            self.article = self.in_article = True
        if self.in_article and tag == "math-renderer":
            self.current = ("js-display-math" in classes, [])
        if self.in_article and tag == "a":
            self.links.append(attrs.get("href", ""))

    def handle_data(self, data):
        if self.current is not None:
            self.current[1].append(data)

    def handle_endtag(self, tag):
        if tag == "math-renderer" and self.current is not None:
            display, parts = self.current
            # HTMLParser decodes the outer HTML layer. GitHub encodes angle
            # brackets and ampersands again inside the component's text.
            value = unescape("".join(parts)).strip()
            delimiter = "$$" if display else "$"
            if display:
                # GitHub's math-fence HTML adds a backslash before a newline
                # following a TeX row break. The rendered row count is unchanged.
                value = re.sub(r"(?<!\\)\\{3}(?=\n)", lambda _: r"\\", value)
            self.formulas.append(
                (display, value.removeprefix(delimiter).removesuffix(delimiter).strip())
            )
            self.current = None
        if tag == "article":
            self.in_article = False


def markdown_formulas(source):
    for match in MATH.finditer(source):
        block = match["block"]
        tex = match["inline"]
        if block is not None:
            tex = "\n".join(line.removeprefix(match["prefix"]) for line in block.splitlines())
        yield ((block is not None, tex.strip()), source.count("\n", 0, match.start()) + 1)


def check_chapter(path, preview):
    source = path.read_text(encoding="utf-8")
    # Catch accidental reintroduction of the Markdown-interpreted display form.
    if re.search(r"^\s*(?:> )?\$\$", source, re.MULTILINE):
        raise ValueError("use a math fence for display math")
    expected = list(markdown_formulas(source))
    observed = preview.formulas
    if not expected:
        raise ValueError("no source formulas found")
    diff = SequenceMatcher(
        a=[formula for formula, _ in expected], b=observed, autojunk=False
    )
    messages = []
    for change, i, j, k, l in diff.get_opcodes():
        if change != "equal":
            lines = ", ".join(str(line) for _, line in expected[i:j]) or "none"
            preview_range = f"{k + 1}–{l}" if k < l else "none"
            messages.append(f"{change} at source lines {lines}, preview formulas {preview_range}")
    if messages:
        raise ValueError(f"{len(expected)} expected, {len(observed)} rendered\n  " + "\n  ".join(messages))
    return f"{len(observed)} formulas match"


def check_index(path, preview, chapters):
    for target in [*(quote(p.name) for p in chapters), f"downloads/{quote(path.name)}"]:
        if not any(target.lower() in link.lower() for link in preview.links):
            raise ValueError(f"missing preview link: {target}")
    return "seven chapter links and download link present"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ref")
    args = parser.parse_args()
    chapters = sorted(ROOT.glob("0[0-6]_*.md"))
    if len(chapters) != 7:
        parser.error(f"expected seven chapters, found {len(chapters)}")

    def check(path):
        request = Request(
            f"{REPO}/blob/{quote(args.ref, safe='')}/{quote(path.name)}",
            headers={"User-Agent": "volterra-wiki-math-check"},
        )
        with urlopen(request, timeout=30) as response:
            preview = Preview()
            preview.feed(response.read().decode("utf-8"))
        if not preview.article:
            raise ValueError("GitHub did not return a rendered Markdown article")
        if path.name == BUNDLE:
            return check_index(path, preview, chapters)
        return check_chapter(path, preview)

    paths = [*chapters, ROOT / BUNDLE]
    ok = True
    with ThreadPoolExecutor(max_workers=4) as pool:
        for path, result in zip(paths, [pool.submit(check, path) for path in paths]):
            try:
                print(f"{path.name}: {result.result()}")
            except (OSError, ValueError) as error:
                print(f"{path.name}: FAIL — {error}")
                ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
