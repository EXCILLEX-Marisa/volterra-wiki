"""Pre-build checks for math fences, local links, and the 38 SVG figures.

Uses Python's standard library; the Node reader remains authoritative for
MathJax rendering and the exact chapter/bundle content comparison.
"""
from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "tools" / "figure_manifest.txt"
BUNDLE = ROOT / "downloads" / "Volterra_Wiki_00-06_完整合订版_GitHub图床.md"
RAW_PREFIX = "https://raw.githubusercontent.com/EXCILLEX-Marisa/volterra-wiki/main/figures/"
SVG_NS = "{http://www.w3.org/2000/svg}svg"
COUNTS = {"00": 4, "01": 17, "02": 4, "03": 4, "04": 2, "05": 3, "06": 4}
IMAGE = re.compile(r"!\[[^\]\n]*\]\(([^)\n]+)\)")
LOCAL_MD = re.compile(r"(?<!!)\[[^\]\n]+\]\(([^)\n]*?\.md(?:\?[^)\n]*)?(?:#[^)\n]*)?)\)")
FENCE = re.compile(r"^[ \t]{0,3}" + chr(96) * 3 + r"([^" + chr(96) + r"\r\n]*)[ \t]*$")
CHINESE_PROSE = re.compile(r"[\u3400-\u9fff]")
BARE_MATH = re.compile(r"(?<!\$)\$(?!`)[^\$\n]{1,120}\$(?!`)")


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def check_fences(path: Path, source: str) -> int:
    active = None
    start = 0
    count = 0
    for lineno, line in enumerate(source.splitlines(), 1):
        match = FENCE.fullmatch(line)
        if not match:
            if active is None:
                require(not BARE_MATH.search(line),
                        f"{path.name}:{lineno}: use GitHub-safe inline math delimiters")
            if active == "math":
                require("$" + chr(96) not in line and not CHINESE_PROSE.search(line),
                        f"{path.name}:{lineno}: prose or inline math inside a math fence")
            continue
        lang = match.group(1).strip()
        if active is None:
            active, start = lang, lineno
            if lang == "math":
                count += 1
        else:
            require(lang == "", f"{path.name}:{lineno}: unclosed prior fenced block")
            active = None
    require(active is None, f"{path.name}:{start}: unclosed fenced block ({active})")
    return count


def check_svg_files(expected: set[str]) -> None:
    actual = {p.name for p in (ROOT / "figures").glob("*.svg")}
    require(actual == expected,
            f"SVG inventory mismatch; missing={sorted(expected - actual)}, extra={sorted(actual - expected)}")
    for name in sorted(expected):
        try:
            root = ET.parse(ROOT / "figures" / name).getroot()
        except ET.ParseError as error:
            raise ValueError(f"{name}: malformed XML: {error}") from error
        require(root.tag == SVG_NS, f"{name}: expected SVG root element")
        try:
            width = float(root.attrib["width"])
            height = float(root.attrib["height"])
            x, y, vw, vh = (float(v) for v in root.attrib["viewBox"].split())
        except (ValueError, KeyError) as error:
            raise ValueError(f"{name}: malformed SVG canvas metadata") from error
        require(width > 0 and height > 0 and vw == width and vh == height
                and x == 0 and y == 0,
                f"{name}: width/height do not match the viewBox")


def check_image(url: str, bundled: bool, path: Path) -> str:
    prefix = RAW_PREFIX if bundled else "figures/"
    require(url.startswith(prefix), f"{path.name}: invalid image URL: {url}")
    name = unquote(url[len(prefix):])
    require(name.endswith(".svg") and Path(name).name == name,
            f"{path.name}: invalid figure reference: {url}")
    return name


def check_links(path: Path, source: str) -> int:
    total = 0
    for match in LOCAL_MD.finditer(source):
        url = urlsplit(match.group(1))
        target = unquote(url.path)
        if not target:
            continue
        resolved = (path.parent / target).resolve()
        require(resolved.is_relative_to(ROOT) and resolved.is_file(),
                f"{path.name}: broken local Markdown link: {match.group(1)}")
        total += 1
    return total


def main() -> int:
    names = [line.strip() for line in read(MANIFEST).splitlines()
             if line.strip() and not line.startswith("#")]
    require(len(names) == 38 and len(set(names)) == 38,
            "figure_manifest.txt must list 38 unique SVG filenames")
    expected = set(names)
    check_svg_files(expected)
    chapters = sorted(ROOT.glob("0[0-6]_*.md"))
    require(len(chapters) == 7 and {p.name[:2] for p in chapters} == set(COUNTS),
            "expected exactly seven chapters (00-06)")
    total_math = total_links = 0
    chapter_figures = set()
    for path in [*chapters, ROOT / "README.md", BUNDLE]:
        source = read(path)
        total_math += check_fences(path, source)
        total_links += check_links(path, source)
        figures = [check_image(m.group(1), path == BUNDLE, path)
                   for m in IMAGE.finditer(source)]
        if path in chapters:
            chapter_id = path.name[:2]
            require(len(figures) == COUNTS[chapter_id],
                    f"{path.name}: expected {COUNTS[chapter_id]} images; got {len(figures)}")
            misplaced = [name for name in figures
                         if not re.fullmatch(rf"{chapter_id}-\d{{2}}_.+\.svg", name)]
            require(not misplaced,
                    f"{path.name}: figure filename chapter prefixes mismatch: {misplaced}")
            require(len(figures) == len(set(figures)),
                    f"{path.name}: duplicate figure references")
            chapter_figures.update(figures)
        if path == BUNDLE:
            require(len(figures) == 38 and set(figures) == expected,
                    f"{path.name}: expected exactly 38 manifest SVG references")
    require(chapter_figures == expected,
            f"chapter figure mismatch; missing={sorted(expected - chapter_figures)}")
    print(f"Validation passed: 7 chapters, 38 SVGs, {total_math} math fences, "
          f"{total_links} local Markdown links.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError) as error:
        print(f"Validation failed: {error}", file=sys.stderr)
        sys.exit(1)
