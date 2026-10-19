#!/usr/bin/env python3
"""The tactile assembly map's Bambu Lab X1C project: the six plates placed on three beds, and its print figures.

Writes ``Build_Files/3D_Printing_Files/Print_Profiles/X1C/Custom_Braille_Embosser_V2_Tactile_Assembly_Map_X1C.3mf``
from the six STL files in ``Build_Files/3D_Printing_Files/Tactile_Assembly_Map/STL/`` and the
settings the project already carries (the owner's: 0.2 mm, 2 walls, 15 % infill, brim ears, Bambu
PLA Basic, textured plate), so the plates and the settings stay the owner's after every change to the
map. Then Bambu Studio's command line slices the project in ``build/`` and the filament and time of
each bed and of the whole map are printed, for the Device Summary and the listing.

How it works. A Bambu Studio project is a 3MF: one XML object a plate, the settings as JSON, and a
plate list that says which objects stand on which bed. The command line loads preset JSON files flat,
with no inheritance, and would slice from the stock presets with no filament density and a 200 mm
bed without a word; a project file carries everything, so the new project is built from the old one's
settings with the new meshes written in. Bambu Studio keeps its beds in a grid of ceil(sqrt(n))
columns, each 1.2 bed widths from the next, rows going down in y; an object is on the bed its
position falls in. The unsliced project the command line exports back carries the bed thumbnails.

Usage:
    python scripts/tactile_assembly_map_x1c.py            # write the project, slice it, print the figures
    python scripts/tactile_assembly_map_x1c.py --figures  # slice the project as it is and print the figures

Local lane: needs trimesh and Bambu Studio 2.8 at its standard path. License: GPL-3.0-or-later
"""

from __future__ import annotations

import argparse
import datetime
import json
import math
import re
import subprocess
import sys
import uuid
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import trimesh

ROOT = Path(__file__).resolve().parent.parent
STL_DIR = ROOT / "Build_Files" / "3D_Printing_Files" / "Tactile_Assembly_Map" / "STL"
PROJECT = ROOT / "Build_Files" / "3D_Printing_Files" / "Print_Profiles" / "X1C" / "Custom_Braille_Embosser_V2_Tactile_Assembly_Map_X1C.3mf"
BUILD = ROOT / "build" / "tactile_assembly_map"
BAMBU = Path(r"C:\Program Files\Bambu Studio\bambu-studio.exe")
BED_MM = 256.0
BED_STRIDE_MM = BED_MM * 1.2
EDGE_MM = 6.0                       # the least room from a plate to the bed's edge
CORNER_MM = (20.0, 30.0)            # the X1C cannot print in its front-left corner (18 x 28 mm)
# Each plate: its STL, its bed, and the centre of the plate on that bed, the notched edge toward the front.
LAYOUT: List[Tuple[str, int, float, float]] = [
    ("Tactile_Assembly_Map_Plate_1_Roller_A.stl", 1, 128.0, 184.0),
    ("Tactile_Assembly_Map_Plate_2_Roller_B.stl", 1, 128.0, 76.0),
    ("Tactile_Assembly_Map_Plate_3_Knob_Lid.stl", 2, 76.5, 128.0),
    ("Tactile_Assembly_Map_Plate_4_Handle.stl", 2, 194.0, 128.0),
    ("Tactile_Assembly_Map_Plate_5_Base_Above.stl", 3, 68.0, 128.0),
    ("Tactile_Assembly_Map_Plate_6_Base_Below.stl", 3, 188.0, 128.0),
]
SETTINGS_PARTS = ["Metadata/project_settings.config", "Metadata/process_settings_1.config", "Metadata/slice_info.config"]
NS = ('xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
      'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
      'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p"')
REL = "http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"
CONTENT_TYPES = ('<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
                 ' <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
                 ' <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>\n'
                 ' <Default Extension="png" ContentType="image/png"/>\n'
                 ' <Default Extension="gcode" ContentType="text/x.gcode"/>\n</Types>\n')


def mesh_xml(mesh_id: int, mesh: trimesh.Trimesh) -> str:
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', f'<model unit="millimeter" xml:lang="en-US" {NS}>',
             ' <metadata name="BambuStudio:3mfVersion">1</metadata>', " <resources>",
             f'  <object id="{mesh_id}" p:UUID="{uuid.uuid4()}" type="model">', "   <mesh>", "    <vertices>"]
    lines += [f'     <vertex x="{x:.6g}" y="{y:.6g}" z="{z:.6g}"/>' for x, y, z in mesh.vertices]
    lines += ["    </vertices>", "    <triangles>"]
    lines += [f'     <triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in mesh.faces]
    lines += ["    </triangles>", "   </mesh>", "  </object>", " </resources>", " <build/>", "</model>", ""]
    return "\n".join(lines)


def object_settings(obj_id: int, mesh_id: int, name: str, faces: int, centre) -> str:
    return "\n".join([
        f'  <object id="{obj_id}">',
        f'    <metadata key="name" value="{name}"/>',
        '    <metadata key="extruder" value="1"/>',
        f'    <metadata face_count="{faces}"/>',
        f'    <part id="{mesh_id}" subtype="normal_part" uuid="{uuid.uuid4()}">',
        f'      <metadata key="name" value="{name}"/>',
        '      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>',
        f'      <metadata key="source_file" value="{name}"/>',
        '      <metadata key="source_object_id" value="0"/>',
        '      <metadata key="source_volume_id" value="0"/>',
        f'      <metadata key="source_offset_x" value="{centre[0]:.6g}"/>',
        f'      <metadata key="source_offset_y" value="{centre[1]:.6g}"/>',
        f'      <metadata key="source_offset_z" value="{centre[2]:.6g}"/>',
        f'      <mesh_stat face_count="{faces}" edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>',
        "    </part>", "  </object>"])


def plate_settings(bed: int, instances: List[Tuple[int, int]]) -> str:
    lines = ["  <plate>", f'    <metadata key="plater_id" value="{bed}"/>',
             f'    <metadata key="plater_name" value="BE V2 Tactile Assembly Map P{bed}"/>',
             '    <metadata key="locked" value="false"/>', '    <metadata key="filament_map_mode" value="Auto For Flush"/>',
             '    <metadata key="filament_maps" value="1"/>', '    <metadata key="filament_volume_maps" value="0"/>']
    for obj_id, ident in instances:
        lines += ["    <model_instance>", f'      <metadata key="object_id" value="{obj_id}"/>',
                  '      <metadata key="instance_id" value="0"/>', f'      <metadata key="identify_id" value="{ident}"/>',
                  "    </model_instance>"]
    lines.append("  </plate>")
    return "\n".join(lines)


def build_project(settings_from: Path, out: Path) -> None:
    """The six plates as a Bambu Studio project, with the settings of the project at settings_from."""
    source = zipfile.ZipFile(settings_from)
    beds = sorted({bed for _, bed, _, _ in LAYOUT})
    cols = math.ceil(math.sqrt(len(beds)))
    today = datetime.date.today().isoformat()
    objects, rels, items, settings_objs = [], [], [], []
    plates: Dict[int, List[Tuple[int, int]]] = {}
    for k, (name, bed, cx, cy) in enumerate(LAYOUT):
        mesh = trimesh.load(STL_DIR / name, force="mesh")
        lo, hi = mesh.bounds
        size, centre = hi - lo, (lo + hi) / 2
        x0, x1, y0, y1 = cx - size[0] / 2, cx + size[0] / 2, cy - size[1] / 2, cy + size[1] / 2
        if not (x0 >= EDGE_MM and x1 <= BED_MM - EDGE_MM and y0 >= EDGE_MM and y1 <= BED_MM - EDGE_MM
                and (x0 >= CORNER_MM[0] or y0 >= CORNER_MM[1])):
            raise ValueError(f"{name} ({size[0]:.1f} x {size[1]:.1f} mm) does not fit bed {bed} at ({cx}, {cy})")
        mesh.vertices = mesh.vertices - centre
        mesh_id, obj_id = 2 * k + 1, 2 * k + 2
        fname = f"3D/Objects/object_{obj_id}.model"
        objects.append((fname, mesh_xml(mesh_id, mesh)))
        rels.append(f' <Relationship Target="/{fname}" Id="rel-{k + 1}" Type="{REL}"/>')
        col, row = (bed - 1) % cols, (bed - 1) // cols
        items.append((obj_id, mesh_id, fname, cx + col * BED_STRIDE_MM, cy - row * BED_STRIDE_MM, size[2] / 2))
        settings_objs.append(object_settings(obj_id, mesh_id, name, len(mesh.faces), centre))
        plates.setdefault(bed, []).append((obj_id, 900 + 11 * (k + 1)))
    model = ['<?xml version="1.0" encoding="UTF-8"?>', f'<model unit="millimeter" xml:lang="en-US" {NS}>',
             ' <metadata name="Application">BambuStudio-02.08.02.61</metadata>', ' <metadata name="BambuStudio:3mfVersion">1</metadata>',
             f' <metadata name="CreationDate">{today}</metadata>', f' <metadata name="ModificationDate">{today}</metadata>', " <resources>"]
    for obj_id, mesh_id, fname, _wx, _wy, _hz in items:
        model += [f'  <object id="{obj_id}" p:UUID="{uuid.uuid4()}" type="model">', "   <components>",
                  f'    <component p:path="/{fname}" objectid="{mesh_id}" p:UUID="{uuid.uuid4()}" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>',
                  "   </components>", "  </object>"]
    model += [" </resources>", f' <build p:UUID="{uuid.uuid4()}">']
    model += [f'  <item objectid="{obj_id}" p:UUID="{uuid.uuid4()}" transform="1 0 0 0 1 0 0 0 1 {wx:.6g} {wy:.6g} {hz:.6g}" printable="1"/>'
              for obj_id, _mesh_id, _fname, wx, wy, hz in items]
    model += [" </build>", "</model>", ""]
    model_settings = ('<?xml version="1.0" encoding="UTF-8"?>\n<config>\n' + "\n".join(settings_objs) + "\n"
                      + "\n".join(plate_settings(b, plates[b]) for b in beds) + "\n</config>\n")
    cut = ('<?xml version="1.0" encoding="utf-8"?>\n<objects>\n'
           + "".join(f' <object id="{k + 1}">\n  <cut_id id="0" check_sum="1" connectors_cnt="0"/>\n </object>\n' for k in range(len(LAYOUT)))
           + "</objects>\n")
    sequence = "{" + ",".join(f'"plate_{b}":{{"nozzle_sequence":[],"optimal_assignment":[],"sequence":[]}}' for b in beds) + "}"
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("_rels/.rels", '<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
                   f' <Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="{REL}"/>\n</Relationships>\n')
        z.writestr("3D/3dmodel.model", "\n".join(model))
        z.writestr("3D/_rels/3dmodel.model.rels", '<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
                   + "\n".join(rels) + "\n</Relationships>\n")
        for fname, xml in objects:
            z.writestr(fname, xml)
        z.writestr("Metadata/model_settings.config", model_settings)
        z.writestr("Metadata/cut_information.xml", cut)
        z.writestr("Metadata/filament_sequence.json", sequence)
        for part in SETTINGS_PARTS:
            z.writestr(part, source.read(part))


def bambu(args: Sequence[str], outdir: Path) -> None:
    """Run Bambu Studio's command line; it reports through result.json in outdir, not the console."""
    if not BAMBU.exists():
        raise FileNotFoundError(f"Bambu Studio not found at {BAMBU}")
    outdir.mkdir(parents=True, exist_ok=True)
    result = outdir / "result.json"
    if result.exists():
        result.unlink()
    subprocess.run([str(BAMBU), *args, "--outputdir", str(outdir)], capture_output=True, timeout=1800, check=False)
    if not result.exists():
        raise RuntimeError("Bambu Studio wrote no result.json")
    report = json.loads(result.read_text(encoding="utf-8"))
    if report.get("return_code", 1) != 0:
        raise RuntimeError(f"Bambu Studio: {report.get('error_string', report)}")


def figures(sliced: Path) -> List[Tuple[int, float, float, int, List[str]]]:
    """(bed, grams, metres, seconds, plate names) for each bed of a sliced project, from its G-code and slice record."""
    z = zipfile.ZipFile(sliced)
    info = z.read("Metadata/slice_info.config").decode("utf-8")
    out = []
    for block in re.findall(r"<plate>.*?</plate>", info, re.DOTALL):
        bed = int(re.search(r'key="index" value="(\d+)"', block).group(1))
        seconds = int(re.search(r'key="prediction" value="(\d+)"', block).group(1))
        names = re.findall(r'<object [^>]*name="Tactile_Assembly_Map_(Plate_\d+)_', block)
        gcode = z.read(f"Metadata/plate_{bed}.gcode").decode("utf-8", "replace")
        grams = float(re.search(r"; total filament weight \[g\] : ([\d.]+)", gcode).group(1))
        metres = float(re.search(r"; total filament length \[mm\] : ([\d.]+)", gcode).group(1)) / 1000
        if re.search(r'key="outside" value="true"', block):
            raise RuntimeError(f"bed {bed}: a plate stands outside the bed")
        out.append((bed, grams, metres, seconds, names))
    return out


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--figures", action="store_true", help="slice the project as it is; do not rewrite it")
    args = ap.parse_args(argv)
    if not args.figures:
        draft = BUILD / "x1c_draft.3mf"
        build_project(PROJECT, draft)
        bambu(["--export-3mf", PROJECT.name, str(draft)], BUILD)
        (BUILD / PROJECT.name).replace(PROJECT)
        print(f"{PROJECT.relative_to(ROOT).as_posix()} written, {PROJECT.stat().st_size // 1024} KB: six plates on three beds")
    bambu(["--slice", "0", "--export-3mf", "x1c_sliced.3mf", str(PROJECT)], BUILD)
    total_g = total_m = total_s = 0.0
    for bed, grams, metres, seconds, names in figures(BUILD / "x1c_sliced.3mf"):
        print(f"bed {bed}: {', '.join(names)}: {grams:.2f} g, {metres:.2f} m, {seconds // 3600} h {seconds % 3600 // 60} min")
        total_g, total_m, total_s = total_g + grams, total_m + metres, total_s + seconds
    print(f"the map: {total_g:.2f} g, {total_m:.2f} m, {int(total_s) // 3600} h {int(total_s) % 3600 // 60} min, ${total_g * 15.99 / 1000:.2f} at $15.99 per kg")
    return 0


if __name__ == "__main__":
    sys.exit(main())
