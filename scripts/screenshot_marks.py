#!/usr/bin/env python3
"""Marks on a screenshot: a red box round each control the reader is to
use, with a numbered badge, and a crop that keeps the marked controls with
some of the page round them. Shared by the two generator-guide screenshot
scripts. The red is the guides' arrow red; the numbers are the order the
caption uses.

License: GPL-3.0-or-later
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFont

RED = (214, 40, 40)
WHITE = (255, 255, 255)
FONT_PATH = Path("C:/Windows/Fonts/arialbd.ttf")
Box = Tuple[float, float, float, float]   # x0, y0, x1, y1 in image pixels


def font(size: int) -> ImageFont.FreeTypeFont:
    if FONT_PATH.exists():
        return ImageFont.truetype(str(FONT_PATH), size)
    return ImageFont.load_default(size=size)


def mark(im: Image.Image, boxes: Sequence[Box], scale: float = 1.0, numbered: bool = True) -> Image.Image:
    """Draw the boxes on a copy of the image. ``scale`` is the image's
    device pixels per CSS pixel; the line and badge grow with it."""
    out = im.convert("RGB")
    d = ImageDraw.Draw(out)
    line = max(3, int(round(3 * scale)))
    pad = int(round(6 * scale))
    badge = int(round(26 * scale))
    f = font(int(round(16 * scale)))
    for i, (x0, y0, x1, y1) in enumerate(boxes, 1):
        d.rounded_rectangle([x0 - pad, y0 - pad, x1 + pad, y1 + pad], radius=int(round(6 * scale)), outline=RED, width=line)
        if numbered:
            bx, by = x0 - pad - badge // 2, y0 - pad - badge // 2
            d.ellipse([bx, by, bx + badge, by + badge], fill=RED)
            tw = d.textlength(str(i), font=f)
            d.text((bx + (badge - tw) / 2, by + badge * 0.08), str(i), font=f, fill=WHITE)
    return out


def crop_round(im: Image.Image, boxes: Sequence[Box], margin: float, min_size: Tuple[int, int] = (0, 0),
               fixed: Optional[Box] = None) -> Image.Image:
    """Crop to the union of the boxes plus a margin (in image pixels), at
    least ``min_size`` wide and tall when the image allows, centred on the
    boxes; or to ``fixed`` when given."""
    if fixed:
        x0, y0, x1, y1 = fixed
    else:
        x0 = min(b[0] for b in boxes) - margin
        y0 = min(b[1] for b in boxes) - margin
        x1 = max(b[2] for b in boxes) + margin
        y1 = max(b[3] for b in boxes) + margin
        for axis, want in ((0, min_size[0]), (1, min_size[1])):
            lo, hi = (x0, x1) if axis == 0 else (y0, y1)
            if hi - lo < want:
                mid = (lo + hi) / 2
                lo, hi = mid - want / 2, mid + want / 2
                if axis == 0:
                    x0, x1 = lo, hi
                else:
                    y0, y1 = lo, hi
    x0, y0 = max(0, int(x0)), max(0, int(y0))
    x1, y1 = min(im.width, int(x1)), min(im.height, int(y1))
    return im.crop((x0, y0, x1, y1))


def mark_and_crop(im: Image.Image, boxes: Sequence[Box], scale: float, margin_css: float = 40,
                  min_css: Tuple[int, int] = (720, 0), fixed_css: Optional[Box] = None, numbered: bool = True) -> Image.Image:
    marked = mark(im, boxes, scale, numbered)
    fixed = tuple(v * scale for v in fixed_css) if fixed_css else None
    return crop_round(marked, boxes, margin_css * scale, (int(min_css[0] * scale), int(min_css[1] * scale)), fixed)


def css_boxes(boxes: Sequence[Box], scale: float) -> List[Box]:
    """Boxes measured in CSS pixels (a browser's bounding boxes) to image pixels."""
    return [(x * scale, y * scale, (x + w) * scale, (y + h) * scale) for x, y, w, h in boxes]
