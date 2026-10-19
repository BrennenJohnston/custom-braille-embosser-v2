# MakerWorld photos

The pictures for the MakerWorld listing, cropped to the same shapes and sizes, one folder for each section of the upload form. `scripts/makerworld_photos.py` makes them from the full-size photographs and from `Photos/renders/`; the top of that script says how it frames each one.

| Folder | Where it goes on the upload form | Size |
|---|---|---|
| `Cover/` | `1_desktop_4x3.jpg` is the desktop cover, `2_mobile_3x4.jpg` the mobile app cover | 1600 × 1200 px; 768 × 1024 px |
| `Real_Photos/` | The real photos, uploaded in the order of their numbers | 1600 × 1200 px |
| `Renders/` | The 3D renderings | 1600 × 1200 px |

For the front, side and top views the form asks for, `01_front.jpg` is the front, the window side. `02_side.jpg` shows the narrow end from above, so it also shows the top of the Handle and the Lid. It is the nearest these photos come to a top view, because none was taken looking straight down; a new photo from directly above would fill that slot exactly.

The sizes are the ones MakerWorld users report the site shows without cropping: 4:3 on the desktop, 3:4 in the app. If the upload form recommends other sizes, change `GALLERY` and `MOBILE` near the top of the script and run it again, naming the folder that holds `Braille Embosser Version 2 Photos`:

    python scripts/makerworld_photos.py --masters "<Official Version 2 folder>"
