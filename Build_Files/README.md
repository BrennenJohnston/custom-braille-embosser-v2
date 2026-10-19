<!--- Open Source Assistive Technology Template: GitHub Build_Files Readme Version 1.2 (2025-Feb-04) --->
# Build files

This folder holds everything you print for the Custom Braille Embosser, Version 2. The device has no firmware and no circuit board; only `3D_Printing_Files` is needed.

## Subfolders

- [`3D_Printing_Files/STL/`](3D_Printing_Files/STL): the nine printed parts, one file each, named as the assembly guide names them. The two braille cylinders are not here; they are generated for your text, at <https://braille-cylinder-stl-generator.vercel.app> with Version 2 chosen under Embosser setup or with the OpenSCAD copy in [`3D_Printing_Files/Embossing_Plates_Customizer/`](3D_Printing_Files/Embossing_Plates_Customizer).
- [`3D_Printing_Files/Print_Profiles/X1C/`](3D_Printing_Files/Print_Profiles/X1C): three sliced Bambu Studio projects for the Bambu Lab X1C, with the settings below: the nine parts on one plate (`Custom_Braille_Embosser_V2_Assembly_X1C.3mf`), the example cylinder pair (`..._Cylinders_X1C.3mf`) and the tactile assembly map's plates (`..._Tactile_Assembly_Map_X1C.3mf`). They hold the tested layouts, so they save arranging the STL files yourself.
- [`3D_Printing_Files/Tactile_Assembly_Map/`](3D_Printing_Files/Tactile_Assembly_Map): the six plates of the tactile assembly map as STL, with their OpenSCAD source and a README.
- [`3D_Printing_Files/Assembly_Reference/`](3D_Printing_Files/Assembly_Reference): `Braille_Embosser_V2_Assembled_Example.stl`, every part in its assembled position as one file. It is a reference for pictures and for anyone remixing the design; it is not a part to print. The cylinders in it are an older sample size, not the 30.8 by 54 mm cylinders the generator makes today.

## Print settings in the X1C projects

| Setting | The nine parts | The cylinder pair | The tactile assembly map |
|---|---|---|---|
| Printer | Bambu Lab X1C, 0.4 mm nozzle, textured PEI plate | the same | the same |
| Layer height | 0.2 mm | 0.12 mm | 0.2 mm |
| Walls | 3, Classic | 3, Arachne | 2, Classic |
| Infill | 15 % | 15 % | 15 % |
| Top and bottom layers | 5 top, 3 bottom | 5 top, 5 bottom | 5 top, 3 bottom |
| Supports | Off | Off | Off |
| Brim | Brim ears | Auto | Brim ears |
| Seam | Aligned | Aligned | Aligned |
| Material | PLA | PLA | PLA |
| Bed used | about 188 x 184 mm | two cylinders standing | two plates: Rollers A and B; the Base with the Knob, Lid and Handle |

Other printers: a printer's default 0.2 mm profile with supports off is all the STL files need. The parts were drawn so that nothing needs supports, seam painting or slower speeds: the cylinders' seam channel, the keyhole shapes and the dot shapes take care of what those used to.

The two cylinders are the exception. They do better at 0.12 mm layers or finer, with at least 3 walls and 15 % infill, and with the Arachne wall generator rather than Classic, which I found gives the braille dots a cleaner shape. Each cylinder prints standing on end.

## File names

The STL files carry the plain names the guide uses. The design files they were exported from carry the engineering names below; the two sets are the same geometry.

| File in this folder | Engineering name |
|---|---|
| `Base.stl` | Body_Base_v2 |
| `Lid.stl` | Body_Top_v2 |
| `Top_Gear_A.stl` | A1_Gear_v2 |
| `Bottom_Gear_A.stl` | A2_Gear_v2 |
| `Top_Gear_B.stl` | B1_Gear_v2 |
| `Bottom_Gear_B.stl` | B2_Gear_v2 |
| `Knob.stl` | Handle_Connector_v2 |
| `Handle.stl` | Handle_v2 |
| `Push-out_Plate_(optional).stl` | Remover_Tool_v2_(optional) |
