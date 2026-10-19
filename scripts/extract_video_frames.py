#!/usr/bin/env python3
"""Contact sheets of a video, and the stills the guide takes from it.

The videos stay outside the repository (the raw assembly recording is
10.6 GB); only stills come in. Two jobs:

``--sheet <video> --every N`` decodes one frame every N seconds and lays the
thumbnails out thirty to a page, each labelled with its time, into
``build/video_sheets/``, so a reviewer can log what happens when and pick
the moments worth a still.

``--extract`` reads every record in ``Documentation/images.json`` whose
origin is a frame (``"kind": "frame"``, ``"source"`` the video's path under
the masters folder, ``"time"`` as ``m:ss`` or ``m:ss.s``), decodes that
frame, and saves it under ``Photos/frames/<name>`` by the same rules as a
photo (1600 px long edge, JPEG quality 85, no EXIF), recording the saved
file's sha256 in the record.

Videos are read with PyAV. The bundled ffmpeg of Playwright cannot decode
these files; PyAV can.

Usage:
    python scripts/extract_video_frames.py --masters "<Official Version 2 folder>" --sheet "Animation/Example_Braille Embosser V2 Assembly.avi" --every 5
    python scripts/extract_video_frames.py --masters "<Official Version 2 folder>" --sheet "Unedited Videos/20261001_181714.mp4" --every 10
    python scripts/extract_video_frames.py --masters "<Official Version 2 folder>" --sheet "Unedited Videos/20261001_181714.mp4" --every 2 --from 3:00 --to 4:00
    python scripts/extract_video_frames.py --masters "<Official Version 2 folder>" --extract

Local lane: needs PyAV and Pillow (never run with ``python -I``).
License: GPL-3.0-or-later
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from fractions import Fraction
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Sequence, Tuple

import av
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.photo_contact_sheets import COLUMNS, GUTTER, LABEL_H, ROWS, THUMB, _font  # noqa: E402
from scripts.photo_import import LONG_EDGE, save_jpeg  # noqa: E402

MANIFEST = ROOT / "Documentation" / "images.json"
SHEETS = ROOT / "build" / "video_sheets"
FRAMES = ROOT / "Photos" / "frames"


def masters_root(arg: Optional[str]) -> Path:
    value = arg or os.environ.get("BE_V2_MASTERS")
    if not value:
        raise SystemExit("name the Official Version 2 folder with --masters or BE_V2_MASTERS")
    root = Path(value)
    if not root.is_dir():
        raise SystemExit(f"{root} is not a folder")
    return root


def parse_time(text: str) -> float:
    """``m:ss`` or ``m:ss.s`` (or plain seconds) as seconds."""
    if ":" in text:
        minutes, seconds = text.split(":", 1)
        return int(minutes) * 60 + float(seconds)
    return float(text)


def fmt_time(seconds: float) -> str:
    return f"{int(seconds // 60)}:{seconds % 60:04.1f}"


def frames_at(video: Path, times: Sequence[float]) -> Iterator[Tuple[float, Image.Image]]:
    """The first decoded frame at or after each time, as PIL images, in
    the order given. Each time is reached by a seek to the keyframe before
    it, then decoding forward."""
    with av.open(str(video)) as container:
        stream = container.streams.video[0]
        stream.thread_type = "AUTO"
        tb = stream.time_base
        for t in times:
            container.seek(int(t / tb), stream=stream, backward=True)
            for frame in container.decode(stream):
                if frame.pts is None:
                    continue
                if frame.pts * tb >= Fraction(t).limit_denominator(1000) - Fraction(1, 1000):
                    yield t, frame.to_image()
                    break
            else:
                raise ValueError(f"{video.name} has no frame at {fmt_time(t)}")


def duration(video: Path) -> float:
    with av.open(str(video)) as container:
        return float(container.duration / av.time_base)


def sheet(video: Path, every: float, start: float = 0.0, end: Optional[float] = None) -> List[Path]:
    total = duration(video)
    end = total if end is None else min(end, total)
    times: List[float] = []
    t = start
    while t <= end:
        times.append(round(t, 3))
        t += every
    per_page = COLUMNS * ROWS
    font = _font(15)
    cell_w, cell_h = THUMB + GUTTER, THUMB + LABEL_H + GUTTER
    pages: List[Path] = []
    SHEETS.mkdir(parents=True, exist_ok=True)
    page_no, page, draw = 0, None, None
    for k, (t, im) in enumerate(frames_at(video, times)):
        if k % per_page == 0:
            if page is not None:
                page.save(pages[-1], "JPEG", quality=88)
            page_no += 1
            page = Image.new("RGB", (COLUMNS * cell_w + GUTTER, ROWS * cell_h + GUTTER + LABEL_H), "white")
            draw = ImageDraw.Draw(page)
            span = f"{fmt_time(start)} to {fmt_time(end)} of {fmt_time(total)}"
            draw.text((GUTTER, 8), f"{video.name}, every {every:g} s, {span}, sheet {page_no}", fill="black", font=font)
            stem = video.stem if start == 0 and end == total else f"{video.stem}-{fmt_time(start).replace(':', 'm')}s"
            pages.append(SHEETS / f"{stem}-sheet-{page_no}.jpg")
        im = im.convert("RGB")
        im.thumbnail((THUMB, THUMB), Image.LANCZOS)
        x = GUTTER + (k % per_page % COLUMNS) * cell_w
        y = GUTTER + LABEL_H + (k % per_page // COLUMNS) * cell_h
        page.paste(im, (x + (THUMB - im.width) // 2, y + (THUMB - im.height) // 2))
        draw.text((x, y + THUMB + 4), fmt_time(t), fill="black", font=font)
    if page is not None:
        page.save(pages[-1], "JPEG", quality=88)
    for p in pages:
        print(f"{p.relative_to(ROOT).as_posix()}")
    print(f"{len(times)} frames on {len(pages)} sheet(s)")
    return pages


def extract(root: Path) -> int:
    records = json.loads(MANIFEST.read_text(encoding="utf-8"))
    wanted = [r for r in records if r["origin"]["kind"] == "frame" and r["use"] == "guide"]
    by_video: Dict[str, List[Dict]] = {}
    for r in wanted:
        if not r["name"]:
            raise SystemExit(f"a frame record at {r['origin'].get('time')} has no name")
        by_video.setdefault(r["origin"]["source"], []).append(r)
    saved = 0
    for source, recs in by_video.items():
        video = root / source
        recs.sort(key=lambda r: parse_time(r["origin"]["time"]))
        times = [parse_time(r["origin"]["time"]) for r in recs]
        for r, (_t, im) in zip(recs, frames_at(video, times)):
            if r.get("crop"):
                im = im.crop(tuple(r["crop"]))
            out = FRAMES / r["name"]
            r["origin"]["imported_sha256"] = save_jpeg(im.convert("RGB"), out, LONG_EDGE)
            print(f"{out.relative_to(ROOT).as_posix()}: {fmt_time(_t)} of {Path(source).name}")
            saved += 1
    MANIFEST.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(f"{saved} still(s) saved")
    return saved


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--masters", help="the Official Version 2 folder (or set BE_V2_MASTERS)")
    ap.add_argument("--sheet", metavar="VIDEO", help="a video's path under the masters folder to lay out as contact sheets")
    ap.add_argument("--every", type=float, default=10.0, help="seconds between the sheet's frames (default 10)")
    ap.add_argument("--from", dest="start", default="0:00", metavar="m:ss", help="where the sheet starts (default the beginning)")
    ap.add_argument("--to", dest="end", default=None, metavar="m:ss", help="where the sheet ends (default the end)")
    ap.add_argument("--extract", action="store_true", help="save every frame record of the registry as a still")
    args = ap.parse_args(argv)
    if not (args.sheet or args.extract):
        ap.error("nothing to do: pass --sheet VIDEO and/or --extract")
    root = masters_root(args.masters)
    if args.sheet:
        video = root / args.sheet
        if not video.exists():
            raise SystemExit(f"{video} does not exist")
        sheet(video, args.every, parse_time(args.start), parse_time(args.end) if args.end else None)
    if args.extract:
        extract(root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
