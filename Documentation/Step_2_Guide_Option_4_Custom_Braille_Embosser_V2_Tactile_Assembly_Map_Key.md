# Tactile Assembly Map Key

What each numbered shape on the tactile assembly map is. The map is six flat printed plates, one line of shapes each, that carry the outline of every face where two parts of the Custom Braille Embosser, Version 2, meet, true to size; this page is the words that go with the numbers.

## 1. How to read the map

- Every shape is drawn as seen from above the embosser standing finished, so a peg's outline lies exactly over the hole it enters: find a peg on a gear shape, then the matching hole on the cylinder shape beside it.
- The plate is the table. A shape rises from it in equal steps, 0.75 mm each in the files here (the `level_step_mm` dial sets it, 0.5 to 1 mm). A part's face, its level 1, stands two steps above the plate; the thing standing on that face (a peg, a bump, a stud, a post, a wall) is one step more, and a thing sunk into the face (a keyhole, a dent, a notch, the Lid's hole) is one step less, whatever its real depth. No shape has more than four levels.
- Below each shape, toward the notched edge of the plate, is its number as a raised numeral 10 mm tall. The same number is cut as a row of notches in that edge, one notch a count, so you can count it with a fingernail.
- Above each shape, its number stands in braille on a small sloped block, the braille facing you: the number sign, then the digits. On a plate with two shapes, a raised line runs from the block down to the shape it names; the line is lower than any shape, so it never reads as part of one. The `braille_labels` dial takes the blocks and lines off for a reader who does not read braille; the numerals and notches stay.
- Hold a plate with the notched edge nearest you: the shapes are then the right way round. Numbers run in the order the steps of the Maker Guide use the parts.
- Cylinder A's shapes have a triangle, Cylinder B's a square, on the side that faces the other cylinder when the two are paired.

## 2. The numbers

| Number | Braille | Part and face | Levels, lowest first | Size (mm) | Goes with | Plate |
|---|---|---|---|---|---|---|
| 1 | ⠼⠁ | Cylinder A, top end | 1: barrel minus the keyhole; 2: barrel minus the countersink mouth; 3: the triangle bump | 30.77 by 30.77 | Top Gear A | 1, Roller A |
| 2 | ⠼⠃ | Top Gear A, peg side | 1: the toothed body minus its notch; 2: the square peg | 32.2 by 32.19 | Cylinder A, top end | 1, Roller A |
| 3 | ⠼⠉ | Cylinder A, bottom end | 1: barrel minus the keyhole; 2: barrel minus the countersink mouth and the dent | 30.77 by 30.77 | Bottom Gear A | 1, Roller A |
| 4 | ⠼⠙ | Bottom Gear A, peg side | 1: the toothed body; 2: the peg; 3: the triangle stud | 32.21 by 32.21 | Cylinder A, bottom end | 1, Roller A |
| 5 | ⠼⠑ | Cylinder B, top end | 1: barrel minus the keyhole; 2: barrel minus the countersink mouth; 3: the square bump | 30.78 by 30.8 | Top Gear B | 2, Roller B |
| 6 | ⠼⠋ | Top Gear B, peg side | 1: the toothed body minus its notch; 2: the peg | 32.09 by 32.09 | Cylinder B, top end | 2, Roller B |
| 7 | ⠼⠛ | Cylinder B, bottom end | 1: barrel minus the keyhole; 2: barrel minus the countersink mouth and the dent | 30.78 by 30.8 | Bottom Gear B | 2, Roller B |
| 8 | ⠼⠓ | Bottom Gear B, peg side | 1: the toothed body; 2: the peg; 3: the square stud | 32.14 by 32.14 | Cylinder B, bottom end | 2, Roller B |
| 9 | ⠼⠊ | Knob, from above | 1: the D-shaped collar; 2: the head and its tab | 23.97 by 18.39 | Top Gear A's pocket (the shaft) and the Handle's cup (the tab) | 3, Knob and Lid |
| 10 | ⠼⠁⠚ | Lid, from above, the post shown through it | 1: the plate minus the Knob hole; 2: the post | 80.78 by 50.8 | the Base's rim; its post into Top Gear B; the Knob through its hole | 3, Knob and Lid |
| 11 | ⠼⠁⠁ | Handle, from above, the cup's keyhole shown through it | 1: the grip and the cup minus the keyhole | 77.46 by 28.5 | the Knob | 4, Handle |
| 12 | ⠼⠁⠃ | Base, from above | 1: the foot; 2: the floor minus its three openings, and the tower walls; 3: the tower walls and the two posts | 98.4 by 68.41 | the roller pair; the Lid | 5, Base from above |
| 13 | ⠼⠁⠉ | Base, from below | 1: the foot minus the three openings; 2: the rim the Base stands on | 98.4 by 68.41 | the Push-out Plate's pegs | 6, Base from below |

## 3. Printing the map

Print `Build_Files/3D_Printing_Files/Tactile_Assembly_Map/Custom_Braille_Embosser_V2_Tactile_Assembly_Map.scad` from OpenSCAD, one plate at a time (set `plate` to 1 to 6 and export), or print the STL of each plate from its `STL/` folder; a sliced Bambu Lab X1C project with the plates is in `Build_Files/3D_Printing_Files/Print_Profiles/X1C/`. The plates are 1.2 mm thick and lie flat on the bed: 0.2 mm layers, any rigid filament, no supports; 0.1 mm layers over the braille blocks (a height-range modifier in the slicer) make the dots smoother. A light colour shows the shapes to a sighted helper too; nothing on the map depends on colour.

Every plate fits a 200 by 200 mm bed. The outlines come from the part files themselves, cut by `scripts/derive_tactile_assembly_map.py`, so a change to a part changes the map.

## 4. What the map is for

The map is a reading aid, not a tool: it does not measure, and nothing fits into it. It reads best with the parts in the other hand, each shape matched to the real face, and does its work before Step 1 of the assembly. The Assembly Guide By Touch says every step for the hands; the map is the picture of the parts it names.
