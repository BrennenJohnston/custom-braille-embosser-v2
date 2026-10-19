# Tactile Assembly Map

Six flat plates, one line of shapes each, that carry the outline of every face where two parts of the embosser meet, true to size, to read by touch before you build. The key to the numbers on the plates is [`Documentation/Step_2_Guide_Option_4_Custom_Braille_Embosser_V2_Tactile_Assembly_Map_Key.md`](../../../Documentation/Step_2_Guide_Option_4_Custom_Braille_Embosser_V2_Tactile_Assembly_Map_Key.md) (also as a PDF beside it).

## Files

| File | What it is |
|---|---|
| `STL/Tactile_Assembly_Map_Plate_1_Roller_A.stl` | Plate 1: Cylinder A's two ends and its two gears, numbers 1 to 4. 170 x 95 mm |
| `STL/Tactile_Assembly_Map_Plate_2_Roller_B.stl` | Plate 2: Cylinder B's two ends and its two gears, numbers 5 to 8. 170 x 95 mm |
| `STL/Tactile_Assembly_Map_Plate_3_Knob_Lid.stl` | Plate 3: the Knob and the Lid, numbers 9 and 10. 129 x 114 mm |
| `STL/Tactile_Assembly_Map_Plate_4_Handle.stl` | Plate 4: the Handle, number 11. 91 x 92 mm |
| `STL/Tactile_Assembly_Map_Plate_5_Base_Above.stl` | Plate 5: the Base from above, number 12. 112 x 132 mm |
| `STL/Tactile_Assembly_Map_Plate_6_Base_Below.stl` | Plate 6: the Base from below, number 13. 112 x 132 mm |
| `Custom_Braille_Embosser_V2_Tactile_Assembly_Map.scad` | The OpenSCAD source, for OpenSCAD on your own computer; it reads the outlines from the shapes file beside it |
| `Custom_Braille_Embosser_V2_Tactile_Assembly_Map_MakerWorld.scad` | The same map as one file with the outlines written in, for MakerWorld's customizer. Generated: never edit by hand |
| `tactile_assembly_map_shapes.scad`, `.json` | The face outlines, cut from the part files by `scripts/derive_tactile_assembly_map.py`. Generated: never edit by hand |
| `../Print_Profiles/X1C/Custom_Braille_Embosser_V2_Tactile_Assembly_Map_X1C.3mf` | A Bambu Studio project for the Bambu Lab X1C with the six plates placed on three beds, written by `scripts/tactile_assembly_map_x1c.py` |

## Printing

Flat on the bed, 0.2 mm layers, any rigid filament, no supports; the sliced X1C project uses 2 walls and 15 % infill. The braille blocks print without supports too (their face leans back 15 degrees, their back is a ramp); 0.1 mm layers over them, set with a height-range modifier in the slicer, make the dots smoother. The six STL files are the map at its standard settings, ready to slice: each fits a 200 by 200 mm bed, the plates are 1.2 mm thick, the shapes rise from them in steps of 0.75 mm (a shape's first level two steps up), the numerals by 1.0 mm, and the braille blocks stand 21 mm tall.

## Changing the map

Both OpenSCAD files carry the same dials, and either makes a plate with your own settings; the STL files need neither.

| Dial | What it changes |
|---|---|
| Which plate | One plate at a time. "All plates (preview)" stands the six in a row; it is larger than a print bed |
| Plate | The plate's thickness, the height of one step (0.5 to 1 mm), the room between two shapes, the room at the plate's edge, the corner radius |
| Labels | The raised numerals' height and size; the width, depth and spacing of the notches that count each number |
| Braille labels | The braille blocks on or off (off also takes away the lines that join them to their shapes); the room between a shape and its block; the blank face below the braille, which lifts it clear of the plate; the width and foot flare of those lines (a line is always one step tall) |

The outlines are not dials: they come from the part files. More room between shapes or at the edge makes a plate larger; the widest plate is 170 mm before any is added. The desktop file opens on "All plates (preview)" and the MakerWorld copy on Plate 1; nothing else differs between them.

## Making the files again

When a part changes, the outlines and the plates change with it:

```
python scripts/derive_tactile_assembly_map.py --preview
python scripts/tactile_assembly_map_key.py
python scripts/tactile_assembly_map_makerworld.py
python scripts/export_tactile_assembly_map_stls.py
python scripts/tactile_assembly_map_x1c.py
```

The first cuts the outlines from the part files (`build/renders/bodies/`, made by `scripts/render_parts.py`) and draws a preview of every face into `build/tactile_assembly_map/`; the second rewrites the key page; the third writes the MakerWorld copy from the source and the outlines; the fourth exports the six plates to `STL/` with OpenSCAD and refuses any plate that is not watertight, one body, flat on the bed, the size and height the source reports, and the same solid from the MakerWorld copy; the fifth places the six plates on three beds in the X1C project and slices it with Bambu Studio's command line for the print time and filament in the Device Summary and the listing. A change to the source alone needs only the last four. The headless check in the OpenSCAD rules applies to both `.scad` files.
