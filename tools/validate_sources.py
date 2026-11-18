"""Pre-build checks for math fences, local links, and the 39 SVG figures.

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
COUNTS = {"00": 5, "01": 17, "02": 4, "03": 4, "04": 2, "05": 3, "06": 4}
IMAGE = re.compile(r"!\[[^\]\n]*\]\(([^)\n]+)\)")
LOCAL_MD = re.compile(r"(?<!!)\[[^\]\n]+\]\(([^)\n]*?\.md(?:\?[^)\n]*)?(?:#[^)\n]*)?)\)")
FENCE = re.compile(r"^[ \t]{0,3}" + chr(96) * 3 + r"([^" + chr(96) + r"\r\n]*)[ \t]*$")
CHINESE_PROSE = re.compile(r"[\u3400-\u9fff]")
BARE_MATH = re.compile(r"(?<!\$)\$(?!`)[^\$\n]{1,120}\$(?!`)")

SECTION_HEADING = re.compile(r"(?m)^#{2,5}\s+([0-6]\.\d+(?:\.\d+)?)(?=\s)")
BOOK_REF = re.compile(
    r"《(0[0-6])》(?:第\s*)?([0-6]\.\d+(?:\.\d+)?"
    r"(?:\s*[、,，—–~～-]\s*[0-6]\.\d+(?:\.\d+)?)*)"
)
NUMBERED_SECTION_REF = re.compile(r"第\s*([0-6]\.\d+(?:\.\d+)?)(?=\s*节)")


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



def check_section_references(chapters: list[Path]) -> int:
    """Check explicit chapter/section citations against actual Markdown headings.

    Only recognize citation syntax (《03》3.6.1, 《03》第 3.6.1、3.11 节,
    or 第 3.10 节). Ignore incidental decimals such as 1.33 ms.
    """
    sources = {path.name[:2]: read(path) for path in chapters}
    sections = {
        match.group(1): chapter_id
        for chapter_id, source in sources.items()
        for match in SECTION_HEADING.finditer(source)
    }
    checked = 0
    for path in chapters:
        source = sources[path.name[:2]]
        for match in BOOK_REF.finditer(source):
            chapter_id = match.group(1)
            for section in re.findall(r"[0-6]\.\d+(?:\.\d+)?", match.group(2)):
                line = source.count("\n", 0, match.start()) + 1
                require(sections.get(section) == chapter_id,
                        f"{path.name}:{line}: broken section reference "
                        f"《{chapter_id}》{section}")
                checked += 1
        for match in NUMBERED_SECTION_REF.finditer(source):
            section = match.group(1)
            line = source.count("\n", 0, match.start()) + 1
            require(section in sections,
                    f"{path.name}:{line}: unknown section reference {section}")
            checked += 1
    return checked


def main() -> int:
    names = [line.strip() for line in read(MANIFEST).splitlines()
             if line.strip() and not line.startswith("#")]
    require(len(names) == 39 and len(set(names)) == 39,
            "figure_manifest.txt must list 39 unique SVG filenames")
    expected = set(names)
    check_svg_files(expected)
    chapters = sorted(ROOT.glob("0[0-6]_*.md"))
    require(len(chapters) == 7 and {p.name[:2] for p in chapters} == set(COUNTS),
            "expected exactly seven chapters (00-06)")
    total_section_refs = check_section_references(chapters)
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
            expected_order = sorted(figures)
            require(figures == expected_order,
                    f"{path.name}: SVG references are out of chapter number order")
            for image_match, image_name in zip(IMAGE.finditer(source), figures):
                caption = re.match(r"^\s*\*图\s*(\d{2}-\d{2})", source[image_match.end():])
                require(caption is not None,
                        f"{path.name}: missing caption after {image_name}")
                require(caption.group(1) == image_name[:5],
                        f"{path.name}: caption {caption.group(1)} does not match {image_name[:5]}")
            chapter_figures.update(figures)
        if path == BUNDLE:
            require(len(figures) == 39 and set(figures) == expected,
                    f"{path.name}: expected exactly 39 manifest SVG references")
    require(chapter_figures == expected,
            f"chapter figure mismatch; missing={sorted(expected - chapter_figures)}")
    print(f"Validation passed: 7 chapters, 39 SVGs, {total_math} math fences, "
          f"{total_links} local Markdown links, {total_section_refs} section references.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError) as error:
        print(f"Validation failed: {error}", file=sys.stderr)
        sys.exit(1)
