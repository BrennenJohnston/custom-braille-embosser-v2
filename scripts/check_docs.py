#!/usr/bin/env python3
"""The documentation gate: the mechanical rules every person-facing Markdown
file must meet, checked over the READMEs and ``Documentation/**/*.md``.

The rules (from the Accessible MakerWorld Documentation Standard, section 1,
and the AI-AT guardrails' documentation bloat scan):

* exactly one H1;
* no skipped heading level and no heading deeper than H3 (``H4_ALLOWED`` is
  empty);
* every image has non-empty alt text that does not start with "image of",
  "photo of" or "picture of";
* no "click here" link text and no "check the console";
* every table cell at most 22 words;
* none of the banned words or hedging phrases outside fenced code blocks,
  backticks and the Makers Making Change boilerplate (the block between
  ``<!-- ABOUT MMC START -->`` and ``<!-- ABOUT MMC END -->`` is their text,
  rewritten by their workflow, so the gate does not judge its words);
* none of the engineering part names the release renamed, as whole
  identifiers, even inside backticks, except in the "File names" sections
  that carry the rename table;
* every relative link and image path resolves (from the file's own folder,
  or from the repository root when it starts with "/", as GitHub reads it),
  including a link whose text wraps onto the next line; a template
  placeholder such as ``<MMCWebLink>`` is left for the owner to fill in;
* no compliance claim ("WCAG compliant", "ADA compliant", "fully accessible").

Any other Markdown file can be checked by naming it on the command line. A
line may keep one word the gate would flag by carrying the comment
``<!-- docs-gate: allow WORD -->`` (a quoted title, a proper name); every such
allowance is a deliberate exception, and the comment says so where it stands.

Usage:
    python scripts/check_docs.py            # prints "<file>:<line>: <rule>: <detail>", exit 1 on any finding
    python scripts/check_docs.py README.md Documentation/Step_2_Guide_Option_3_Custom_Braille_Embosser_V2_Maker_Guide.md

Standard library only. Ported from the Braille Sign STL Generator's gate.
License: GPL-3.0-or-later
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

PROJECT_ROOT = Path(__file__).resolve().parent.parent

H4_ALLOWED: set = set()
MAX_CELL_WORDS = 22
BANNED_WORDS = ("leverage", "utilize", "ensure", "facilitate", "streamline",
                "comprehensive", "robust", "seamless", "harness", "empower")
HEDGES = ("please note that", "it is important to understand", "it should be noted",
          "keep in mind that", "it's worth mentioning")
# The engineering part names the release renamed, as regular expressions for
# whole identifiers. The guide uses the plain names (Base, Lid, Top Gear A ...).
RETIRED = ("Body_Base_v2", "Body_Top_v2", r"[AB][12]_Gear_v2", "Handle_Connector_v2",
           "Handle_v2", "Remover_Tool_v2", "Gear Remover")
# (file, H2 title): the sections where the retired names belong, the rename tables.
RETIRED_ALLOWED_SECTIONS = {
    ("Build_Files/README.md", "File names"),
}
COMPLIANCE = ("wcag compliant", "ada compliant", "fully accessible")
ALT_PREFIXES = ("image of", "photo of", "picture of")
ALLOW = re.compile(r"<!--\s*docs-gate:\s*allow\s+([^>]+?)\s*-->", re.I)
THIRD_PARTY_START = "<!-- ABOUT MMC START -->"
THIRD_PARTY_END = "<!-- ABOUT MMC END -->"

_IMAGE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
_LINK = re.compile(r"(?<!!)\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
_HEADING = re.compile(r"^(#{1,6})\s+(\S.*)$")
_FENCE = re.compile(r"^\s*(```|~~~)")
_CODE_SPAN = re.compile(r"`[^`]*`")
_PLACEHOLDER = re.compile(r"^<[A-Za-z]+>$")


@dataclass
class Finding:
    path: Path
    line: int
    rule: str
    detail: str

    def relative(self) -> str:
        try:
            return self.path.resolve().relative_to(PROJECT_ROOT).as_posix()
        except ValueError:
            return str(self.path)

    def format(self) -> str:
        return f"{self.relative()}:{self.line}: {self.rule}: {self.detail}"


def gate_files(root: Path = PROJECT_ROOT) -> List[Path]:
    files = [root / "README.md", root / "Build_Files" / "README.md", root / "Design_Files" / "README.md",
             root / "Video_Tutorials" / "README.md"]
    files += sorted((root / "Documentation").rglob("*.md"))
    return [f for f in files if f.exists()]


def _prose_lines(text: str) -> List[tuple]:
    """(line number, text with fenced code, backtick spans and the third-party
    boilerplate block blanked)."""
    out = []
    in_fence = False
    in_third_party = False
    for n, line in enumerate(text.splitlines(), 1):
        if THIRD_PARTY_START in line:
            in_third_party = True
        if THIRD_PARTY_END in line:
            in_third_party = False
            out.append((n, ""))
            continue
        if _FENCE.match(line):
            in_fence = not in_fence
            out.append((n, ""))
            continue
        out.append((n, "" if in_fence or in_third_party else _CODE_SPAN.sub(" ", line)))
    return out


def _allowed(line: str) -> set:
    return {w.strip().lower() for m in ALLOW.finditer(line) for w in m.group(1).split(",")}


def check_file(path: Path) -> List[Finding]:
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    rel = path.resolve().relative_to(PROJECT_ROOT).as_posix() if path.resolve().is_relative_to(PROJECT_ROOT) else path.name
    findings: List[Finding] = []
    prose = _prose_lines(text)
    raw_lines = text.splitlines()

    # Headings, and the retired part names (inside backticks too, outside fences).
    h1_lines = []
    prev_level = 0
    in_fence = False
    section = ""
    for n, line in enumerate(raw_lines, 1):
        if _FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = _HEADING.match(line)
        if m:
            level = len(m.group(1))
            if level <= 2:
                section = m.group(2).strip()
            if level == 1:
                h1_lines.append(n)
            if prev_level and level > prev_level + 1:
                findings.append(Finding(path, n, "heading-level", f"H{level} after H{prev_level}"))
            if level >= 4 and rel not in H4_ALLOWED:
                findings.append(Finding(path, n, "heading-level", f"H{level} is deeper than this project's documents go"))
            prev_level = level
        if (rel, section) in RETIRED_ALLOWED_SECTIONS:
            continue
        allowed = _allowed(line)
        for name in RETIRED:
            for hit in re.finditer(rf"(?<!\w){name}(?!\w)", line):
                if hit.group(0).lower() not in allowed:
                    findings.append(Finding(path, n, "retired-word", hit.group(0)))
    if len(h1_lines) != 1:
        findings.append(Finding(path, h1_lines[1] if len(h1_lines) > 1 else 1, "one-h1", f"{len(h1_lines)} H1 headings"))

    # Images and links over the whole prose, so a link whose text wraps is still seen.
    blanked = "\n".join(line for _, line in prose)
    for m in _IMAGE.finditer(blanked):
        n = blanked.count("\n", 0, m.start()) + 1
        alt, target = " ".join(m.group(1).split()), m.group(2)
        if not alt:
            findings.append(Finding(path, n, "alt-text", f"image {target} has no alt text"))
        elif alt.lower().startswith(ALT_PREFIXES):
            findings.append(Finding(path, n, "alt-text-prefix", f"alt text starts with '{' '.join(alt.split()[:2])}'"))
        _check_target(path, n, target, findings)
    for m in _LINK.finditer(blanked):
        n = blanked.count("\n", 0, m.start()) + 1
        label, target = " ".join(m.group(1).split()), m.group(2)
        if label.lower() == "click here":
            findings.append(Finding(path, n, "link-text", "link text says 'click here'"))
        _check_target(path, n, target, findings)

    # Words and claims, line by line (outside code).
    for n, line in prose:
        if not line:
            continue
        allowed = _allowed(raw_lines[n - 1])
        low = line.lower()
        if "click here" in low and not any(m.group(1).strip().lower() == "click here" for m in _LINK.finditer(line)):
            findings.append(Finding(path, n, "link-text", "'click here'"))
        if "check the console" in low and "check the console" not in allowed:
            findings.append(Finding(path, n, "console", "'check the console'"))
        for word in BANNED_WORDS:
            if word in allowed:
                continue
            if re.search(rf"\b{word}\b", low):
                findings.append(Finding(path, n, "banned-word", word))
        for phrase in HEDGES:
            if phrase in low and phrase not in allowed:
                findings.append(Finding(path, n, "banned-word", phrase))
        for claim in COMPLIANCE:
            if claim in low and claim not in allowed:
                findings.append(Finding(path, n, "compliance-claim", claim))

    # Table cells.
    for n, line in enumerate(raw_lines, 1):
        s = line.strip()
        if not (s.startswith("|") and s.endswith("|")):
            continue
        cells = s.strip("|").split("|")
        if all(re.fullmatch(r"\s*:?-{3,}:?\s*", c) for c in cells):
            continue
        for cell in cells:
            words = len(cell.split())
            if words > MAX_CELL_WORDS:
                findings.append(Finding(path, n, "table-cell", f"{words} words in one cell (at most {MAX_CELL_WORDS})"))
                break
    return findings


def _check_target(path: Path, n: int, target: str, findings: List[Finding]) -> None:
    if target.startswith(("http://", "https://", "mailto:", "#")) or _PLACEHOLDER.match(target):
        return
    rel = target.split("#", 1)[0]
    if not rel:
        return
    base = PROJECT_ROOT if rel.startswith("/") else path.parent
    if not (base / rel.lstrip("/")).exists():
        findings.append(Finding(path, n, "broken-link", f"{target} does not resolve"))


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    files: Iterable[Path] = [Path(a) for a in args] if args else gate_files()
    findings: List[Finding] = []
    for f in files:
        findings += check_file(f)
    for finding in findings:
        print(finding.format())
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
