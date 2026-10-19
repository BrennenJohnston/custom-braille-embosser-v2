#!/usr/bin/env python3
"""The screenshots of the OpenSCAD Generator Guide.

Two sources. The OpenSCAD window captures that scripts/openscad_gui_capture.py
makes with ``--scrolls 0,-3`` (``build/screens/openscad-window-N.png``, the
maximised window with the Customizer at its top, then three wheel notches
down) are cropped and marked here: the window's four panels, the
Editor's toolbar buttons, the Gears and Card Sides choices, the text lines,
the Cylinders to Generate choices, the card-thickness preset, the preview
and the console. The crop boxes are pixel positions in a 1920 x 1032
capture; if the captures change size or layout, look at them and set the
boxes again. And
the braille translator at https://www.branah.com/braille-translator is
driven in a headless browser for the two translation pictures.

Pictures go to ``Photos/screens/screen-osc-*.png`` and ``screen-branah-*.png``
and are registered in images.json.

Usage:
    python scripts/openscad_guide_screenshots.py            # both sources
    python scripts/openscad_guide_screenshots.py --branah   # the translator only
    python scripts/openscad_guide_screenshots.py --openscad # the window crops only

Local lane: needs Pillow, Playwright for Python with Microsoft Edge, and
the window captures. License: GPL-3.0-or-later
"""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.render_parts import register  # noqa: E402
from scripts.screenshot_marks import crop_round, css_boxes, mark, mark_and_crop  # noqa: E402

OUT = ROOT / "Photos" / "screens"
CAPTURES = ROOT / "build" / "screens"
BRANAH = "https://www.branah.com/braille-translator"
SAMPLE_TEXT = "Washington"
SCALE = 2
Box = Tuple[int, int, int, int]

# Each OpenSCAD picture: the capture it comes from, the boxes to mark
# (x0, y0, x1, y1 in capture pixels), the crop, and an enlargement for
# small strips. Measured on the 2026-10-07 captures, after the Customizer
# took the web app's layout and five descriptions were shortened. A
# Customizer box holds the whole setting (its name, description and control),
# so its line never strikes through the description, and starts left of the
# panel, so its badge never covers the name; a group's title bar is left
# unmarked, and the crop starts at the bar.
OPENSCAD_SHOTS: List[Dict] = [
    {"name": "screen-osc-01-window", "capture": 1, "boxes": [(0, 46, 440, 1010), (448, 46, 1540, 860), (1548, 46, 1912, 1010), (448, 866, 955, 1010)],
     "crop": (-30, -30, 1950, 1062), "zoom": 1,
     "shows": "the whole OpenSCAD window with the generator open: the Editor, the preview, the Customizer and the Console marked"},
    {"name": "screen-osc-02-toolbar", "capture": 1, "boxes": [(234, 68, 258, 94), (265, 68, 289, 94), (301, 68, 325, 94)],
     "crop": (90, 56, 440, 106), "zoom": 3,
     "shows": "the Editor's toolbar with the Preview, Render and Export as STL buttons marked"},
    {"name": "screen-osc-03-text-lines", "capture": 1, "boxes": [(1545, 336, 1891, 383)],
     "crop": (1500, 307, 1920, 488), "zoom": 2,
     "shows": "the Customizer's Text Input group: its title, the hint that names the translator, and the Line 1 field holding braille, marked"},
    {"name": "screen-osc-04-choices", "capture": 1, "boxes": [(1545, 147, 1891, 208), (1545, 241, 1891, 302)],
     "crop": (1500, 116, 1920, 329), "zoom": 2,
     "shows": "the Customizer's first two groups, Gears and Card Sides, with the integrated gears and double sided lists marked, both at Off"},
    {"name": "screen-osc-05-card-thickness", "capture": 2, "boxes": [(1545, 824, 1891, 859)],
     "crop": (1500, 796, 1920, 867), "zoom": 2,
     "shows": "the Customizer's Expert Mode - Card Thickness group with the paper thickness preset list at 0.4mm marked"},
    {"name": "screen-osc-06-preview", "capture": 1, "boxes": [],
     "crop": (448, 46, 1540, 860), "zoom": 1,
     "shows": "the preview after F5, close up: the two cylinders side by side, raised dots on Cylinder A and dimples on Cylinder B"},
    {"name": "screen-osc-07-console", "capture": 1, "boxes": [(452, 886, 950, 1004)],
     "crop": (430, 850, 970, 1020), "zoom": 2,
     "shows": "the Console after a preview, with Compile and preview finished near its end"},
    {"name": "screen-osc-08-cylinders", "capture": 1, "boxes": [(1545, 708, 1891, 756), (1545, 767, 1891, 854)],
     "crop": (1500, 680, 1920, 877), "zoom": 2,
     "shows": "the Customizer's Expert Mode - Cylinders to Generate group with the render both plates list at On and the plate type list marked"},
]


PAD = 40   # white border round each capture, so a badge at the window's edge is not cut off


def openscad_shots() -> List[Path]:
    from PIL import ImageOps

    made = []
    for shot in OPENSCAD_SHOTS:
        im = ImageOps.expand(Image.open(CAPTURES / f"openscad-window-{shot['capture']}.png").convert("RGB"), PAD, (255, 255, 255))
        boxes = [(x0 + PAD, y0 + PAD, x1 + PAD, y1 + PAD) for x0, y0, x1, y1 in shot["boxes"]]
        crop = tuple(v + PAD for v in shot["crop"])
        marked = mark(im, boxes, 1.0) if boxes else im
        picture = crop_round(marked, boxes or [crop], 0, fixed=crop)
        if shot["zoom"] > 1:
            picture = picture.resize((picture.width * shot["zoom"], picture.height * shot["zoom"]), Image.LANCZOS)
        out = OUT / f"{shot['name']}.png"
        picture.save(out, optimize=True)
        register(shot["name"], out, {"kind": "screen", "ids": ["cylinder-a", "cylinder-b"], "shows": shot["shows"]})
        print(f"{out.relative_to(ROOT).as_posix()} {picture.width}x{picture.height}")
        made.append(out)
    return made


def branah_shots() -> List[Path]:
    from playwright.sync_api import sync_playwright

    made = []
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 900}, device_scale_factor=SCALE)
        page.goto(BRANAH, wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_timeout(3000)
        english = page.locator("textarea#english")
        english.fill(SAMPLE_TEXT)
        page.wait_for_timeout(500)

        def shoot(selectors: Sequence, **crop) -> Image.Image:
            boxes = []
            for sel in selectors:
                b = page.locator(sel).first.bounding_box()
                boxes.append((b["x"], b["y"], b["width"], b["height"]))
            png = page.screenshot(full_page=False)
            return mark_and_crop(Image.open(io.BytesIO(png)), css_boxes(boxes, SCALE), SCALE, **crop)

        shots = [
            ("screen-branah-01-type", ["textarea#english", "label[for='grade2']", "label[for='brailleUnicode']", "input[value='Translate'], :text-is('Translate')"],
             "the translator with Washington typed in the English box; the Grade 2 and Unicode choices and the Translate button marked"),
        ]
        for name, sels, shows in shots:
            picture = shoot(sels, min_css=(900, 0), margin_css=30)
            out = OUT / f"{name}.png"
            picture.save(out, optimize=True)
            register(name, out, {"kind": "screen", "ids": ["cylinder-a", "cylinder-b"], "shows": shows})
            print(f"{out.relative_to(ROOT).as_posix()} {picture.width}x{picture.height}")
            made.append(out)
        page.locator("label[for='grade2']").click()
        page.locator("label[for='brailleUnicode']").click()
        page.locator("input[value='Translate'], :text-is('Translate')").first.click()
        page.wait_for_timeout(1500)
        picture = shoot(["textarea#braille"], min_css=(900, 0), margin_css=30)
        out = OUT / "screen-branah-02-copy.png"
        picture.save(out, optimize=True)
        register("screen-branah-02-copy", out, {"kind": "screen", "ids": ["cylinder-a", "cylinder-b"],
                                                 "shows": "the translator's Braille box filled with the Unicode braille for Washington, ready to copy"})
        print(f"{out.relative_to(ROOT).as_posix()} {picture.width}x{picture.height}")
        made.append(out)
        print("braille:", page.locator("textarea#braille").input_value())
        browser.close()
    return made


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--branah", action="store_true", help="the translator pictures only")
    ap.add_argument("--openscad", action="store_true", help="the OpenSCAD window crops only")
    args = ap.parse_args(argv)
    OUT.mkdir(parents=True, exist_ok=True)
    if not args.branah:
        openscad_shots()
    if not args.openscad:
        branah_shots()
    return 0


if __name__ == "__main__":
    sys.exit(main())
