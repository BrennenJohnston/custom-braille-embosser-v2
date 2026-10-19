# MakerWorld customizer: the two cylinder files

These two files are the cylinder generator as MakerWorld's Parametric Model Maker runs it: one `.scad` file per customizer, with nothing beside it. Each makes the Version 2 pair, Cylinder A and Cylinder B, from braille you paste in; they differ in the gears. The standard file is the customizer inside the embosser's MakerWorld listing; the fixed-gear file is here for anyone who wants to upload it to a listing of their own.

| File | What it makes |
|---|---|
| `Braille_Cylinder_STL_Generator_MakerWorld_v2.scad` | Standard cylinders for the standard housing: the gears print separately and push into the keyed holes. |
| `Braille_Cylinder_STL_Generator_MakerWorld_v2_Fixed_Gears.scad` | Fixed-gear cylinders for the fixed-gear housing: each comes out with its top and bottom gears on. |

The desktop copy in [`../OpenSCAD_Offline_Alternative/`](../OpenSCAD_Offline_Alternative) makes both kinds from one file, with a Gears switch that reads two gear files from its `assets` folder. MakerWorld cannot load files beside the `.scad`, so with that switch on the gears would be missing; the fixed-gear file carries the gear shapes inside itself instead. That makes it about 3 MB, and a render of both cylinders takes about twice as long as the standard file's (about 6 seconds against 3, measured on 2026-10-07). The cylinder size and the key clearances are not offered in it, because the gears fit only the 30.8 by 54 mm cylinder and a fixed-gear cylinder has no keyed holes.

Both files lay out their settings the way the web app does: Card Sides, the braille for the front, the braille for the back, then the Expert Mode groups in the web app's order. The [OpenSCAD Generator Guide](../../../../Documentation/Step_1_Guide_Option_2_Custom_Braille_Embosser_V2_OpenSCAD_Generator_Guide.md) explains the settings.

## Where these files come from

Both are copies of the `makerworld/` folder of [`braille-cylinder-stl-generator-openscad`](https://github.com/BrennenJohnston/braille-cylinder-stl-generator-openscad), and `VENDORED.json` records where they came from and their SHA-256 hashes. The fixed-gear file is generated there, from the standard file and the two gear meshes, by `scripts/build_makerworld_fixed_gears.py`. A change belongs in that repository: an edit to a copy here no longer matches its recorded hash. License: PolyForm Noncommercial 1.0.0, the generator's license, in [`../OpenSCAD_Offline_Alternative/LICENSE_PolyForm_Noncommercial_1.0.0.md`](../OpenSCAD_Offline_Alternative/LICENSE_PolyForm_Noncommercial_1.0.0.md).
