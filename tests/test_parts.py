"""``Documentation/parts.json``: the facts about every part, pinned to the
files they describe (quick lane, standard library only).
License: GPL-3.0-or-later"""

from __future__ import annotations

import hashlib
from pathlib import Path

from scripts.parts_table import COLUMNS, guide_block, load_parts, replace_block, table_markdown

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STL = PROJECT_ROOT / "Build_Files" / "3D_Printing_Files" / "STL"
PRINTED = 9
CYLINDERS = 2


def test_parts_json_has_every_part_once() -> None:
    parts = load_parts()
    assert len(parts) == PRINTED + CYLINDERS
    assert len({p["id"] for p in parts}) == len(parts)
    assert len({p["name"] for p in parts}) == len(parts)
    for p in parts:
        assert p["count"] == 1
        assert len(p["size_mm"]) == 3 and all(v > 0 for v in p["size_mm"])
        assert p["volume_mm3"] > 0
        assert p["colour_in_photos"]
        assert p["old_names"], f"{p['id']} lists no old name"


def test_every_printed_part_is_a_file_with_the_recorded_hash() -> None:
    files = [p for p in load_parts() if p["file"]]
    assert len(files) == PRINTED
    for p in files:
        path = STL / p["file"]
        assert path.exists(), f"{p['file']} is not in {STL.relative_to(PROJECT_ROOT).as_posix()}"
        assert hashlib.sha256(path.read_bytes()).hexdigest() == p["master_sha256"], f"{p['file']} changed"
    assert sorted(f.name for f in STL.glob("*.stl")) == sorted(p["file"] for p in files)


def test_cylinders_come_from_the_generator() -> None:
    cylinders = [p for p in load_parts() if not p["file"]]
    assert [p["name"] for p in cylinders] == ["Cylinder A", "Cylinder B"]
    for p in cylinders:
        assert p["source"].startswith("https://")
        assert p["size_mm"] == [30.8, 30.8, 54.0]


def test_table_round_trips_through_the_guide_markers() -> None:
    table = table_markdown(load_parts())
    lines = table.splitlines()
    assert lines[0] == "| " + " | ".join(COLUMNS) + " |"
    assert len(lines) == 2 + PRINTED + CYLINDERS
    assert "| Push-out Plate (optional) | `Push-out_Plate_(optional).stl` |" in table
    assert "110.0" not in table, "no step uses a size, so the table carries none (D67)"
    page = "# Guide\n\n<!-- parts-table -->\nold\n<!-- /parts-table -->\n\nmore\n"
    written = replace_block(page, table)
    assert guide_block(written) == table
    assert written.endswith("<!-- /parts-table -->\n\nmore\n")
