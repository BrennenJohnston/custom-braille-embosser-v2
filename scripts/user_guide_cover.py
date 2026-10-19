#!/usr/bin/env python3
"""The User Guide's cover panel: four pictures of what the guide covers.

Under the User Guide's title and its one-sentence introduction the cover
shows, in a two-by-two grid, the embosser standing, a card going in, the
embossed card, and the rollers lifted out to change the message, so a
reader sees at once what the guide is for (the owner's request,
2026-10-06). The panel is ``Photos/visual/visual-user-guide-cover.jpg``,
registered in images.json; the pictures in it are the registry's own.

Usage:
    python scripts/user_guide_cover.py

Local lane: needs Pillow. License: GPL-3.0-or-later
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.render_parts import register  # noqa: E402

PHOTOS = ROOT / "Photos"
OUT = PHOTOS / "visual" / "visual-user-guide-cover.jpg"
# (group/name, what it stands for), in reading order: the embosser, a card
# going in, the card that comes out, the rollers out for a new message.
PANELS: List[Tuple[str, str]] = [
    ("finished/finished-standing.jpg", "the embosser"),
    ("renders/render-use-03-card-into-slit.png", "a card going into the slit"),
    ("finished/finished-with-embossed-card.jpg", "an embossed card"),
    ("finished/finished-swap-rollers-lifted-out.jpg", "the rollers out, for a new message"),
]
TILE_W, TILE_H, GAP, BORDER = 800, 600, 24, 4
BACKGROUND = "white"
RULE = "#444444"


def tile(path: Path) -> Image.Image:
    """The picture scaled to fill its tile, centre-cropped."""
    with Image.open(path) as im:
        im = im.convert("RGB")
        scale = max(TILE_W / im.width, TILE_H / im.height)
        im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
        x0 = (im.width - TILE_W) // 2
        y0 = (im.height - TILE_H) // 2
        return im.crop((x0, y0, x0 + TILE_W, y0 + TILE_H))


def main(argv: Optional[Sequence[str]] = None) -> int:
    page = Image.new("RGB", (2 * TILE_W + 3 * GAP, 2 * TILE_H + 3 * GAP), BACKGROUND)
    for k, (name, _) in enumerate(PANELS):
        col, row = k % 2, k // 2
        x = GAP + col * (TILE_W + GAP)
        y = GAP + row * (TILE_H + GAP)
        page.paste(tile(PHOTOS / name), (x, y))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    page.save(OUT, "JPEG", quality=88, optimize=True)
    register("visual-user-guide-cover", OUT, {"kind": "panel", "ids": ["base", "lid", "knob", "handle", "cylinder-a", "cylinder-b",
                                                                        "top-gear-a", "bottom-gear-a", "top-gear-b", "bottom-gear-b"],
                                               "shows": "four pictures in a grid: " + "; ".join(what for _, what in PANELS)})
    print(f"{OUT.relative_to(ROOT).as_posix()} {page.size[0]} x {page.size[1]} px, {OUT.stat().st_size // 1024} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
