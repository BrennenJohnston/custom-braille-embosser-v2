"""The tactile assembly map's data and its key page stay consistent.

The shapes file is cut from the part meshes by scripts/derive_tactile_assembly_map.py
(a local-lane script); this test checks what the repository ships: thirteen
numbered faces, at most four levels each in exact 0.5 mm steps, every face on
one plate of the map, and the key page written from the same data.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MAP_DIR = PROJECT_ROOT / "Build_Files" / "3D_Printing_Files" / "Tactile_Assembly_Map"
SHAPES_JSON = MAP_DIR / "tactile_assembly_map_shapes.json"
SHAPES_SCAD = MAP_DIR / "tactile_assembly_map_shapes.scad"
MAP_SCAD = MAP_DIR / "Custom_Braille_Embosser_V2_Tactile_Assembly_Map.scad"
KEY_PAGE = PROJECT_ROOT / "Documentation" / "Step_2_Guide_Option_4_Custom_Braille_Embosser_V2_Tactile_Assembly_Map_Key.md"
MAKERWORLD_SCAD = MAP_DIR / "Custom_Braille_Embosser_V2_Tactile_Assembly_Map_MakerWorld.scad"
STEP_MM = 0.5
MAX_LEVELS = 4
FACE_COUNT = 13
MIN_HOLE_MM2 = 0.5  # MIN_AREA_MM2 in scripts/derive_tactile_assembly_map.py


def all_faces() -> list:
    return json.loads(SHAPES_JSON.read_text(encoding="utf-8"))["faces"]


def faces() -> list:
    """The faces on the map; the gears' hub sides are drawn in the Visual Assembly Guide only."""
    return [f for f in all_faces() if f["map"]]


def test_thirteen_faces_in_exact_steps() -> None:
    fs = faces()
    assert [f["n"] for f in fs] == list(range(1, FACE_COUNT + 1))
    for f in all_faces():
        assert 1 <= len(f["levels"]) <= MAX_LEVELS, f"face {f['n']} has {len(f['levels'])} levels"
        for i, lv in enumerate(f["levels"]):
            assert lv["height_mm"] == (i + 1) * STEP_MM, f"face {f['n']} level {i + 1} is {lv['height_mm']} mm"
            assert lv["polygons"], f"face {f['n']} level {i + 1} is empty"
        w, h = f["size_mm"]
        assert 10 < w < 120 and 10 < h < 80, f"face {f['n']} is {w} x {h} mm"


def _ring_area(points: list) -> float:
    return abs(sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(points, points[1:] + points[:1]))) / 2


def test_no_level_has_a_sliver_hole_or_a_shared_corner() -> None:
    """Two outlines that share a boundary once left holes a thousandth of a
    millimetre wide, touching corner to corner, and Plate 4 was not watertight."""
    for f in all_faces():
        for i, lv in enumerate(f["levels"], 1):
            corners = [tuple(p) for points, _ in lv["polygons"] for p in points]
            assert len(corners) == len(set(corners)), f"face {f['n']} level {i} uses a corner twice"
            for points, paths in lv["polygons"]:
                for hole in paths[1:]:
                    area = _ring_area([points[k] for k in hole])
                    assert area >= MIN_HOLE_MM2, f"face {f['n']} level {i} has a hole of {area:.4f} mm2"


def test_scad_shapes_carry_every_face() -> None:
    text = SHAPES_SCAD.read_text(encoding="utf-8")
    assert f"TACTILE_STEP_MM = {STEP_MM}" in text
    for f in faces():
        assert f'[{f["n"]}, "{f["name"]}"' in text, f"face {f['n']} is not in the .scad shapes"


def test_map_scales_the_levels_by_its_own_step() -> None:
    """The shapes file's heights are units of TACTILE_STEP_MM; the map's dial sets the printed step."""
    text = MAP_SCAD.read_text(encoding="utf-8")
    assert "level_step_mm = 0.75; // [0.5:0.25:1.0]" in text
    assert "(lvl[0] / step_mm) * level_step_mm" in text


def _dots(cell: str) -> list:
    """A Unicode braille character as its dot numbers (bit n of the code point is dot n + 1)."""
    bits = ord(cell) - 0x2800
    return [d + 1 for d in range(6) if bits & (1 << d)]


def test_braille_digits_are_the_standard_cells() -> None:
    """The map writes each number from its own digit table; a wrong dot there would mislabel a shape."""
    text = MAP_SCAD.read_text(encoding="utf-8")
    sign = re.search(r"^number_sign = (\[.*?\]);", text, re.M)
    digits = re.search(r"^digit_dots = (\[.*?\]);", text, re.M)
    assert sign and digits, "the map file lacks its braille digit table"
    assert json.loads(sign.group(1)) == _dots("⠼")
    assert json.loads(digits.group(1)) == [_dots(c) for c in "⠚⠁⠃⠉⠙⠑⠋⠛⠓⠊"]


def test_every_face_is_on_one_plate() -> None:
    sys.path.insert(0, str(PROJECT_ROOT))
    from scripts.tactile_assembly_map_key import plates_from_scad

    plates = plates_from_scad()
    assert sorted(plates) == list(range(1, FACE_COUNT + 1))
    assert set(plates.values()) == {1, 2, 3, 4, 5, 6}


def test_makerworld_copy_is_current_and_stands_alone() -> None:
    result = subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts" / "tactile_assembly_map_makerworld.py"), "--check"],
                            capture_output=True, text=True, cwd=str(PROJECT_ROOT))
    assert result.returncode == 0, result.stdout + result.stderr
    text = MAKERWORLD_SCAD.read_text(encoding="utf-8")
    assert not [line for line in text.splitlines() if line.startswith(("include", "use"))], "MakerWorld cannot read a second file"
    assert "\nplate = 1; //" in text, "the MakerWorld copy opens on Plate 1"
    # The outlines stand after [Hidden], or the customizer would offer them as dials.
    assert text.index("/* [Hidden] */") < text.index("tactile_faces = [")


def test_every_plate_has_its_stl() -> None:
    names = sorted(p.name for p in (MAP_DIR / "STL").glob("*.stl"))
    assert names == ["Tactile_Assembly_Map_Plate_1_Roller_A.stl", "Tactile_Assembly_Map_Plate_2_Roller_B.stl",
                     "Tactile_Assembly_Map_Plate_3_Knob_Lid.stl", "Tactile_Assembly_Map_Plate_4_Handle.stl",
                     "Tactile_Assembly_Map_Plate_5_Base_Above.stl", "Tactile_Assembly_Map_Plate_6_Base_Below.stl"]
    for p in (MAP_DIR / "STL").glob("*.stl"):
        assert not p.read_bytes().startswith(b"solid"), f"{p.name} is a text STL; the export writes binary"


def test_key_page_is_current() -> None:
    result = subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts" / "tactile_assembly_map_key.py"), "--check"],
                            capture_output=True, text=True, cwd=str(PROJECT_ROOT))
    assert result.returncode == 0, result.stdout + result.stderr
    assert KEY_PAGE.exists()
