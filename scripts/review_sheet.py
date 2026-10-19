#!/usr/bin/env python3
"""The review sheet: everything the owner has to read before a release, on
one page, so the review can happen away from the repository.

For each document that shows pictures, every picture it uses is shown as a small
copy beside the file's name, its alt text and its caption, in the order the
document shows them and under the heading it sits in. After the pictures
come the by-touch strings: every "By touch", "Find it by touch", "Find them
by touch" and "Which way round" paragraph, by heading. Last, the
conventions and warnings from the string register.

The sheet is a working file, not part of the release: it is written to
``build/review/REVIEW_SHEET.md`` and printed to ``build/review/REVIEW_SHEET.pdf``
by the guide builder in compact form, with no record. The owner answers
with "sign all" or a list of changes by picture number, step or string id;
the answers go into ``Documentation/images.json`` (``alt_status``) and
the string register, a working file kept outside the repository (its
section is left out when the file is absent).

Usage:
    python scripts/review_sheet.py            # write the page and print the PDF
    python scripts/review_sheet.py --no-pdf   # the page only

Local lane: needs Pillow and a browser for the PDF. License: GPL-3.0-or-later
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts import build_assembly_guide_pdf as builder  # noqa: E402

DOCS = (("Step_1_Guide_Option_1_Custom_Braille_Embosser_V2_Web_Generator_Guide.md", "Web generator guide"),
        ("Step_1_Guide_Option_2_Custom_Braille_Embosser_V2_OpenSCAD_Generator_Guide.md", "OpenSCAD generator guide"),
        ("Step_2_Guide_Option_1_Custom_Braille_Embosser_V2_Visual_Assembly_Guide.md", "Visual assembly guide"),
        ("Step_2_Guide_Option_2_Custom_Braille_Embosser_V2_Assembly_Guide_By_Touch.md", "Assembly guide by touch"),
        ("Step_2_Guide_Option_3_Custom_Braille_Embosser_V2_Maker_Guide.md", "Maker guide"),
        ("Step_2_Guide_Option_4_Custom_Braille_Embosser_V2_Tactile_Assembly_Map_Key.md", "Tactile assembly map key"),
        ("Step_3_Guide_Custom_Braille_Embosser_V2_User_Guide.md", "User guide"),
        ("Custom_Braille_Embosser_V2_Device_Summary.md", "Device summary"),
        ("Custom_Braille_Embosser_V2_Design_Rationale.md", "Design rationale"),
        ("Custom_Braille_Embosser_V2_MakerWorld_Listing.md", "MakerWorld listing"))
REGISTER = ROOT.parent.parent / "local-projects" / "custom-braille-embosser-v2-materials" / "NOTES" / "06_STRING_REGISTER.md"
OUT_DIR = ROOT / "build" / "review"
THUMBS = OUT_DIR / "thumbs"
MD = OUT_DIR / "REVIEW_SHEET.md"
PDF = OUT_DIR / "REVIEW_SHEET.pdf"
THUMB_W = 720
TOUCH_LABELS = ("**By touch:**", "By touch:", "Find it by touch:", "Find them by touch:", "Which way round:")
IMAGE_LINE = re.compile(r"^!\[([^\]]*)\]\(([^)\s]+)\)\s*$")
HEADING = re.compile(r"^(#{1,3}) (.+?)\s*$")


def thumb(src: Path) -> Path:
    THUMBS.mkdir(parents=True, exist_ok=True)
    out = THUMBS / (src.stem + ".jpg")
    with Image.open(src) as im:
        im = im.convert("RGB")
        im.thumbnail((THUMB_W, THUMB_W), Image.LANCZOS)
        im.save(out, "JPEG", quality=82, optimize=True)
    return out


def paragraphs(text: str) -> List[Tuple[str, str]]:
    """(current heading, block) for every block of a page, in order; a block
    is a heading line, an image line, or a paragraph joined into one line."""
    out: List[Tuple[str, str]] = []
    heading = ""
    current: List[str] = []
    in_fence = False

    def flush() -> None:
        nonlocal current
        if current:
            out.append((heading, " ".join(current)))
            current = []

    for line in text.replace("\r\n", "\n").split("\n"):
        if line.strip().startswith("```"):
            in_fence = not in_fence
            flush()
            continue
        if in_fence:
            continue
        s = line.strip()
        if not s:
            flush()
            continue
        h = HEADING.match(s)
        if h:
            flush()
            heading = h.group(2)
            out.append((heading, s))
            continue
        if IMAGE_LINE.match(s) or s.startswith("<!--"):
            flush()
            out.append((heading, s))
            continue
        current.append(s)
    flush()
    return out


def pictures_of(page: Path) -> List[Tuple[str, str, Path, str]]:
    """(heading, alt, picture path, caption) for every picture of a page."""
    blocks = paragraphs(page.read_text(encoding="utf-8"))
    out = []
    for i, (heading, block) in enumerate(blocks):
        m = IMAGE_LINE.match(block)
        if not m:
            continue
        caption = ""
        if i + 1 < len(blocks):
            nxt = blocks[i + 1][1]
            if not (IMAGE_LINE.match(nxt) or HEADING.match(nxt) or nxt.startswith(("<!--", "**", "|", "1. ", "- "))):
                caption = nxt
        out.append((heading, m.group(1), (page.parent / m.group(2)).resolve(), caption))
    return out


def touch_of(page: Path) -> List[Tuple[str, str]]:
    """(heading, paragraph) for every by-touch paragraph of a page."""
    return [(h, b) for h, b in paragraphs(page.read_text(encoding="utf-8")) if b.startswith(TOUCH_LABELS)]


def register_lines(prefixes: Sequence[str]) -> List[str]:
    if not REGISTER.exists():
        return []
    lines = REGISTER.read_text(encoding="utf-8").splitlines()
    return [re.sub(r"\s*<!--.*?-->", "", ln[2:]) for ln in lines if ln.startswith("- ") and ln[2:].startswith(tuple(prefixes))]


def sheet() -> str:
    # Headings stay short: a heading that wraps loses its space in the PDF's
    # outline, which the builder's check refuses.
    out = ["# Review sheet, Version 2 guides", "",
           "Every picture the three guides use, beside its file name, its alt text (the short description a screen reader "
           "reads first) and its caption (the longer description printed under it); then every by-touch paragraph; then the "
           "conventions and warnings. Read, and answer with \"sign all\" or a list of changes by picture number, by step, or "
           "by string id. A picture's alt and caption are signed by setting its `alt_status` to `reviewed` in "
           "`Documentation/images.json`; a string is signed in the string register.", ""]
    n = 0
    for file, head in DOCS:
        page = ROOT / "Documentation" / file
        if not page.exists():
            continue
        entries = pictures_of(page)
        if not entries:
            continue
        out += [f"## Pictures in the {head.lower()}", ""]
        # The picture comes right after its heading, so the builder keeps
        # the two on one page; the context rides in the caption.
        for heading, alt, src, caption in entries:
            n += 1
            t = thumb(src)
            out += [f"### Picture {n}", "",
                    f"![{alt}]({Path('thumbs') / t.name})", "",
                    f"Under the heading: {heading}. File: {src.name}. Alt: {alt} Caption: {caption or '(none)'}", ""]
    for file, head in DOCS:
        page = ROOT / "Documentation" / file
        if not page.exists():
            continue
        entries = touch_of(page)
        if not entries:
            continue
        out += [f"## By touch, {head.lower()}", ""]
        for k, (heading, para) in enumerate(entries, 1):
            out += [f"### {head}, touch {k}", "", f"Under the heading: {heading}.", "", para, ""]
    register = register_lines(("X-", "W-"))
    if register:
        out += ["## Conventions and warnings, from the register", ""]
        for line in register:
            out += [f"- {line}"]
    out.append("")
    return "\n".join(out)


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--no-pdf", action="store_true", help="write the page only")
    args = ap.parse_args(argv)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    text = sheet()
    MD.write_text(text, encoding="utf-8", newline="\n")
    print(f"{MD.relative_to(ROOT).as_posix()}: {text.count('![')} pictures, {text.count('touch ')} by-touch entries")
    if args.no_pdf:
        return 0
    # The builder's own functions print and verify the sheet; it is pointed
    # at this page by its module globals and writes no record, so the
    # stale-print lane never asks for the sheet.
    builder.DOCUMENT, builder.COMPACT_DOC = "review-sheet", True
    builder.SOURCE, builder.OUT_PDF, builder.RECORD = MD.resolve(), PDF.resolve(), None
    builder.HEAD, builder.TITLE = "Review sheet", f"Review sheet, {builder.PROJECT}"
    builder.SCRATCH.mkdir(parents=True, exist_ok=True)
    html_path = builder.SCRATCH / "review-sheet.html"
    html_text = builder.document_html(builder.printable_markdown(), None)
    html_path.write_text(html_text, encoding="utf-8")
    builder.print_to_pdf(html_path, PDF)
    counts = builder.verify(PDF, html_text, {})
    print(f"{PDF.relative_to(ROOT).as_posix()}: {counts['pages']} pages, {counts['pictures']} pictures, "
          f"{PDF.stat().st_size / 1024:.0f} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
