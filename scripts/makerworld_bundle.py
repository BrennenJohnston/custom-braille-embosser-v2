#!/usr/bin/env python3
"""The two ZIP files the MakerWorld listing needs beside its model files.

MakerWorld's model-file slot takes 3D and CAD files only (stl, 3mf, step,
scad and the like) and refuses a PDF, so the documents travel inside a ZIP,
which the slot does take. This script writes, under ``build/makerworld/``:

* ``Custom_Braille_Embosser_V2_Guides.zip``: the seven step-numbered guides
  as tagged PDFs (``Step_1_...`` to ``Step_3_...``);
* ``Custom_Braille_Embosser_V2_OpenSCAD_Generator.zip``: the offline cylinder
  generator with its assets, README, changelog and license.

The Device Summary, the Design Rationale and the bill of materials wait for a
later release (the owner, 2026-10-06, D70). The STL files, the 3MF projects
and the tactile map's OpenSCAD file upload on their own; the listing's field
11 lists what goes where.

Usage:
    python scripts/makerworld_bundle.py

Standard library only. License: GPL-3.0-or-later
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path
from typing import List, Optional, Sequence

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "makerworld"
DOCS = ROOT / "Documentation"
GENERATOR = ROOT / "Build_Files" / "3D_Printing_Files" / "Embossing_Plates_Customizer" / "OpenSCAD_Offline_Alternative"


def guide_files() -> List[Path]:
    pdfs = sorted(DOCS.glob("Step_*_Guide_*Custom_Braille_Embosser_V2_*.pdf"))
    if len(pdfs) != 7:
        raise FileNotFoundError(f"expected the seven step guides, found {len(pdfs)}")
    return pdfs


def generator_files() -> List[Path]:
    return sorted(p for p in GENERATOR.rglob("*") if p.is_file())


def write_zip(out: Path, files: Sequence[Path], base: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for f in files:
            if not f.exists():
                raise FileNotFoundError(f)
            z.write(f, f.relative_to(base).as_posix())
    return out


def main(argv: Optional[Sequence[str]] = None) -> int:
    made = [
        write_zip(OUT / "Custom_Braille_Embosser_V2_Guides.zip", guide_files(), DOCS),
        write_zip(OUT / "Custom_Braille_Embosser_V2_OpenSCAD_Generator.zip", generator_files(), GENERATOR.parent),
    ]
    for z in made:
        with zipfile.ZipFile(z) as zf:
            names = zf.namelist()
        print(f"{z.relative_to(ROOT).as_posix()}: {len(names)} files, {z.stat().st_size // 1024} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
