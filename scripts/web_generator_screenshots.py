#!/usr/bin/env python3
"""The screenshots of the Web Generator Guide: the cylinder generator at
https://braille-cylinder-stl-generator.vercel.app driven step by step in a
headless browser, each screenshot cropped round the controls that step
uses, with a red box and a number on each (scripts/screenshot_marks.py).

The pictures go to ``Photos/screens/screen-web-NN-<name>.png`` and are
registered in images.json. The text typed is "Washington", the text of the
example cylinder pair shipped in Build_Files, so the guide's pictures and
the example print agree. Run it again whenever the app changes.

Usage:
    python scripts/web_generator_screenshots.py            # the live site
    python scripts/web_generator_screenshots.py --url http://127.0.0.1:5000

Local lane: needs Playwright for Python with Microsoft Edge (the
``msedge`` channel) and Pillow. License: GPL-3.0-or-later
"""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.render_parts import register  # noqa: E402
from scripts.screenshot_marks import css_boxes, mark_and_crop  # noqa: E402

OUT = ROOT / "Photos" / "screens"
URL = "https://braille-cylinder-stl-generator.vercel.app"
VIEWPORT = {"width": 1280, "height": 900}
SCALE = 2                       # device pixels per CSS pixel: crisp text when printed
SAMPLE_TEXT = "Washington"
GENERATE_TIMEOUT_MS = 240_000


def boxes_of(page, selectors: Sequence) -> List:
    """One box a selector; a tuple of selectors is one box round all of them (a control with its label)."""
    out = []
    for sel in selectors:
        group = sel if isinstance(sel, tuple) else (sel,)
        xs0, ys0, xs1, ys1 = [], [], [], []
        for s in group:
            loc = page.locator(s).first
            b = loc.bounding_box()
            if b is None:
                raise RuntimeError(f"{s} has no box")
            xs0.append(b["x"]); ys0.append(b["y"]); xs1.append(b["x"] + b["width"]); ys1.append(b["y"] + b["height"])
        out.append((min(xs0), min(ys0), max(xs1) - min(xs0), max(ys1) - min(ys0)))
    return out


def shoot(page, selectors: Sequence[str], scroll_to: Optional[str] = None, settle_ms: int = 400, **crop) -> Image.Image:
    """Scroll the first (or the named) control to the middle of the window,
    screenshot the window, mark the controls and crop round them."""
    first = selectors[0][0] if isinstance(selectors[0], tuple) else selectors[0]
    anchor = page.locator(scroll_to or first).first
    anchor.evaluate("el => el.scrollIntoView({block: 'center', inline: 'nearest'})")
    page.wait_for_timeout(settle_ms)
    boxes = boxes_of(page, selectors)
    png = page.screenshot(full_page=False)
    im = Image.open(io.BytesIO(png))
    return mark_and_crop(im, css_boxes(boxes, SCALE), SCALE, **crop)


def fieldset_with_legend(text: str) -> str:
    return f"fieldset:has(> legend:has-text('{text}'))"


def steps(page) -> List[Dict]:
    """Each entry: the file name, what the picture shows, the parts it is
    about, and a function that drives the page and returns the picture."""
    submenu = "button.expert-submenu-toggle[aria-controls='{}']"

    def s01():
        page.goto(URL, wait_until="networkidle", timeout=60_000)
        page.wait_for_timeout(1500)
        return shoot(page, ["#embosser-setup-fieldset"], min_css=(1100, 760), margin_css=60)

    def s02():
        page.locator("#embosser_version_2").check()
        page.wait_for_timeout(800)
        return shoot(page, ["#embosser-version-selection", "#embosser_version_2"], min_css=(900, 0))

    def s03():
        return shoot(page, [fieldset_with_legend("Card sides"), fieldset_with_legend("Gears")], scroll_to=fieldset_with_legend("Card sides"), min_css=(900, 0))

    def s04():
        page.locator("#auto-text").fill(SAMPLE_TEXT)
        page.wait_for_timeout(500)
        return shoot(page, [("label[for='auto-text']", "#auto-text"), ("label:has(#placement_mode_auto), #placement_mode_auto",)], min_css=(900, 0))

    def s05():
        return shoot(page, ["#language-table"], min_css=(900, 0))

    def s06():
        page.locator("#translate-to-braille-btn").click()
        page.wait_for_timeout(2500)
        return shoot(page, ["#translate-to-braille-btn", ("label[for='braille-unicode']", "#braille-unicode")], min_css=(900, 0))

    def s07():
        page.locator("#expert-toggle").click()
        page.wait_for_timeout(800)
        return shoot(page, ["#expert-toggle", submenu.format("expert-panel-card-thickness")], min_css=(900, 0))

    def s08():
        page.locator(submenu.format("expert-panel-card-thickness")).click()
        page.wait_for_timeout(800)
        return shoot(page, ["#expert-panel-card-thickness"], min_css=(900, 0))

    def s09():
        page.locator("#action-btn").evaluate("el => el.scrollIntoView({block: 'center'})")
        return shoot(page, ["#action-btn"], min_css=(900, 300))

    def s10():
        page.locator("#action-btn").click()
        page.locator("#download-stl-btn").wait_for(state="visible", timeout=GENERATE_TIMEOUT_MS)
        page.wait_for_timeout(3000)
        return shoot(page, ["#viewer", "#pair-status"], scroll_to="#viewer", min_css=(1100, 0), margin_css=30)

    def s11():
        return shoot(page, ["#download-stl-btn"], min_css=(900, 300))

    def s12():
        page.locator("#card_sides_double").check()
        page.wait_for_timeout(800)
        back = fieldset_with_legend("Back of Card")
        return shoot(page, [back], min_css=(900, 0))

    def s13():
        page.locator("#card_sides_single").check()
        page.locator("#gear_mode_fixed").check()
        page.wait_for_timeout(800)
        return shoot(page, [fieldset_with_legend("Gears"), ("label[for='gear_mode_fixed'], label:has(#gear_mode_fixed), #gear_mode_fixed",)], min_css=(900, 0))

    return [
        {"name": "screen-web-01-open", "shows": "the generator's page as it opens, the Embosser setup choices at the top of the form", "fn": s01},
        {"name": "screen-web-02-version-2", "shows": "the Embosser version choice with Version 2 chosen", "fn": s02},
        {"name": "screen-web-03-sides-and-gears", "shows": "the Card sides and Gears choices at their defaults, single-sided and standard gears", "fn": s03},
        {"name": "screen-web-04-text", "shows": "the text box with Washington typed in it, automatic placement chosen", "fn": s04},
        {"name": "screen-web-05-language", "shows": "the language and grade list, English UEB grade 2", "fn": s05},
        {"name": "screen-web-06-translate", "shows": "the Translate to Braille button and the braille field filled with the translation", "fn": s06},
        {"name": "screen-web-07-expert-mode", "shows": "the Show Expert Mode button opened, with the Card Thickness submenu below it", "fn": s07},
        {"name": "screen-web-08-card-thickness", "shows": "the Card Thickness choices, 0.4 mm, 0.3 mm and custom", "fn": s08},
        {"name": "screen-web-09-generate", "shows": "the Generate STL button", "fn": s09},
        {"name": "screen-web-10-preview", "shows": "the 3D preview of the two generated cylinders and the status line under it", "fn": s10},
        {"name": "screen-web-11-download", "shows": "the Download STL button after a successful run", "fn": s11},
        {"name": "screen-web-12-double-sided", "shows": "the Back of Card text box that choosing Double-sided unlocks", "fn": s12},
        {"name": "screen-web-13-one-piece-rollers", "shows": "the Gears choice set to one-piece rollers", "fn": s13},
    ]


def main(argv: Optional[Sequence[str]] = None) -> int:
    global URL
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--url", default=URL, help="the generator's address (default: the live site)")
    ap.add_argument("--only", action="append", default=[], metavar="NN", help="one step by its two-digit number (repeatable)")
    args = ap.parse_args(argv)
    URL = args.url
    OUT.mkdir(parents=True, exist_ok=True)
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page(viewport=VIEWPORT, device_scale_factor=SCALE)
        for step in steps(page):
            nn = step["name"].split("-")[2]
            picture = step["fn"]()
            if args.only and nn not in args.only:
                continue
            out = OUT / f"{step['name']}.png"
            picture.save(out, optimize=True)
            register(step["name"], out, {"kind": "screen", "ids": ["cylinder-a", "cylinder-b"], "shows": step["shows"]})
            print(f"{out.relative_to(ROOT).as_posix()} {picture.width}x{picture.height} {out.stat().st_size // 1024} KB")
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
