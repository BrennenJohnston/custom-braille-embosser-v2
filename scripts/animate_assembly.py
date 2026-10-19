#!/usr/bin/env python3
"""The assembly as moving pictures: every part travels along its own path
into its seat, in the order of the guide's steps, rendered by OpenSCAD.

One OpenSCAD file is generated from the placed bodies in
``build/renders/bodies/`` (the split assembled example plus the example
cylinders). In it, time ``$t`` runs 0 to 1 over the whole assembly; each
step owns an equal slice of it. During the first 70 % of its slice the
step's parts travel in a straight line from a start pose (lifted clear of
the seat, along the way they go in) to the seat, eased; then they hold
while the camera glides to the next step's framing. A part fades in over
the first tenth of the step that brings it. Parts that have not yet
arrived are not drawn. The last step turns the Handle a full turn and the
rollers with it, clockwise seen from above (the owner's correction of
2026-10-06). The camera is set from inside the file (``$vpt``,
``$vpr``, ``$vpd``), which the command line honours when no ``--camera``
is given, so each step is framed on its own action.

Three things are made from that one file:

* the step stills for the Visual Assembly Guide, frozen at the start of
  the step with the moving part at its start pose and a red dashed arrow
  from its leading face to the point it enters (``-D still=<step>``), into
  ``build/animation/stills/`` for scripts/visual_guide.py to letter;
* one keyframe per step half way along its travel, ``Photos/renders/
  render-step-NN-moving.png``, registered in images.json (the start and
  seated frames go to ``build/animation/keyframes/``);
* the animation frames (``openscad --animate N``), joined by PyAV into an
  H.264 MP4 per step and one of the whole assembly under Video_Tutorials/,
  and on request a small GIF for a release page.

Usage:
    python scripts/animate_assembly.py --stills          # stills + keyframes (about a minute)
    python scripts/animate_assembly.py --video           # every frame, then the MP4s (several minutes)
    python scripts/animate_assembly.py --video --gif
    python scripts/animate_assembly.py --short           # the 28-second MP4 and GIF for MakerWorld, from the frames

Local lane: needs the OpenSCAD 2026.01.03 nightly, Pillow and PyAV (never
run with ``python -I``). License: GPL-3.0-or-later
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.render_parts import PART_COLOURS, find_openscad, register, split_bodies  # noqa: E402

ANIM = ROOT / "build" / "animation"
FRAMES = ANIM / "frames"
STILLS = ANIM / "stills"
KEYFRAMES = ANIM / "keyframes"
RENDERS = ROOT / "Photos" / "renders"
VIDEOS = ROOT / "Video_Tutorials"
SCAD = ANIM / "assembly.scad"
IMGSIZE = "1600,1200"
VIEW_ROT = (60, 0, 35)   # the three-quarter view from the left front, as every stage render
FPS = 24
FRAMES_PER_STEP = 96     # four seconds a step (the owner found two too fast, 2026-10-06)
TRAVEL = 0.7             # the part moves during this share of its step; the camera glides after
FADE = 0.1
ARROW_COLOUR = "#d62828"
STEP_NAME = "Custom_Braille_Embosser_V2_Assembly_Animation"

Vec = Tuple[float, float, float]
# The rollers are built in the air and come down into the Base at step 8.
LIFT = 110.0
# A step: the bodies it moves, the offset (mm) they start from, the arrow
# from the moving part's leading face (at its seat) to the point it enters,
# and the camera (centre, distance) that frames the action. The camera and
# the arrow are given in the seat frame; the script adds the displacement
# of the steps still to come (the slide of step 7, the lift of step 8).
ROLLER_A = ["cylinder-a", "top-gear-a", "bottom-gear-a"]
ROLLER_B = ["cylinder-b", "top-gear-b", "bottom-gear-b"]
STEPS: List[Dict] = [
    {"n": 1, "title": "Cylinder A", "move": ["cylinder-a"], "offset": (0, 0, 0),
     "cam": ((-30, 0, 28), 260)},
    {"n": 2, "title": "Top Gear A", "move": ["top-gear-a"], "offset": (0, 0, 60),
     "arrow": ((-30, 0, 38.8), (-30, 0, 56.8)), "cam": ((-30, 0, 62), 360)},
    {"n": 3, "title": "Bottom Gear A", "move": ["bottom-gear-a"], "offset": (0, 0, -60),
     "arrow": ((-30, 0, 14.8), (-30, 0, -0.2)), "cam": ((-30, 0, -3), 360)},
    {"n": 4, "title": "Cylinder B", "move": ["cylinder-b"], "offset": (0, 0, 0),
     "cam": ((-15, 0, 28), 350)},
    {"n": 5, "title": "Top Gear B", "move": ["top-gear-b"], "offset": (0, 0, 60),
     "arrow": ((0, 0, 38.8), (0, 0, 56.8)), "cam": ((-15, 0, 62), 420)},
    {"n": 6, "title": "Bottom Gear B", "move": ["bottom-gear-b"], "offset": (0, 0, -60),
     "arrow": ((0, 0, 14.8), (0, 0, -0.2)), "cam": ((-15, 0, -3), 420)},
    {"n": 7, "title": "Pair the rollers", "move": ROLLER_A, "offset": (-30, 0, 0),
     "arrow": ((-13.9, 0, 27), (-16.5, 0, 27)), "cam": ((-25, 0, 27), 350)},
    {"n": 8, "title": "Into the Base", "move": ROLLER_A + ROLLER_B, "offset": (0, 0, LIFT), "appear": ["base"],
     "arrow": ((-30, 0, -10.2), (-30, 0, 64.3)), "arrow_b": ((0, 0, -10.2), (0, 0, 64.3)), "cam": ((-15, 0, 71), 580)},
    {"n": 9, "title": "Knob", "move": ["knob"], "offset": (0, 0, 50),
     "arrow": ((-30, 0, 55.2), (-30, 0, 63.8)), "cam": ((-15, 0, 50), 460)},
    {"n": 10, "title": "Lid", "move": ["lid"], "offset": (0, 0, 50),
     "arrow": ((0, 0, 53.0), (0, 0, 63.8)), "cam": ((-15, 0, 45), 440)},   # the Lid's post into Top Gear B's hub
    {"n": 11, "title": "Handle", "move": ["handle"], "offset": (0, 0, 50),
     "arrow": ((-30, 0, 66.5), (-30, 0, 82.6)), "cam": ((-15, 0, 68), 520)},
    {"n": 12, "title": "Turn to test", "move": [], "offset": (0, 0, 0), "turn": True,
     "cam": ((-15, 0, 43), 440)},
]
AXES = {"a": (-30.0, 0.0), "b": (0.0, 0.0)}


def _vec(v: Sequence[float]) -> str:
    return "[" + ", ".join(f"{x:g}" for x in v) + "]"


def _add(*vs: Sequence[float]) -> Vec:
    return tuple(sum(v[i] for v in vs) for i in range(3))  # type: ignore[return-value]


def later_displacement(k: int, pid: str) -> Vec:
    """Where the part still stands, relative to its seat, at the start of
    step k: the offsets of every later step that moves it."""
    return _add((0, 0, 0), *[s["offset"] for s in STEPS if s["n"] > k and pid in s["move"]])


def column(pid: str) -> Optional[str]:
    if pid.endswith("-a") or pid in ("knob", "handle"):
        return "a"
    return "b" if pid.endswith("-b") else None


def scad_text(bodies: Dict[str, Path]) -> str:
    """The animation file: one module per body, a pose per step, the
    camera per step, the travel arrows of the stills."""
    n = len(STEPS)
    first_step: Dict[str, int] = {}
    for s in STEPS:
        for pid in s["move"] + s.get("appear", []):
            first_step.setdefault(pid, s["n"])
    unplaced = sorted(set(bodies) - set(first_step))
    if unplaced:
        raise ValueError(f"no step brings {unplaced}")
    cams = [s["cam"] for s in STEPS]
    cam_t = [_add(c[0], later_displacement(s["n"], s["move"][0]) if s["move"] else (0, 0, 0)) for s, c in zip(STEPS, cams)]
    lines = [
        "// Generated by scripts/animate_assembly.py. Do not edit; rerun the script.",
        "still = -1;   // -1 animates; a step number freezes at that step's start with its travel arrow",
        "time = -1;    // -1 takes the time from $t (--animate); 0..1 fixes it (a -D on $t itself lands too late for the camera)",
        f"steps = {n};",
        f"travel = {TRAVEL}; fade = {FADE};",
        "function clamp01(x) = max(0, min(1, x));",
        "function smooth(x) = x * x * (3 - 2 * x);",
        "function now() = still >= 0 ? still - 1 : (time >= 0 ? time : $t) * steps;",
        "function prog(k) = smooth(clamp01((now() - (k - 1)) / travel));   // 0 before step k moves, 1 once seated",
        "function present(k) = now() >= (k - 1) - 1e-9;",
        "function alpha(k) = still >= 0 ? 1 : clamp01((now() - (k - 1)) / fade);",
        f"function turn() = prog({n}) * 360;",
        "// The camera: each step's framing, gliding to the next during the hold.",
        f"cam_t = [{', '.join(_vec(c) for c in cam_t)}];",
        f"cam_d = [{', '.join(f'{c[1]:g}' for c in cams)}];",
        "function cam_k() = min(steps - 1, floor(now()));",
        "function cam_f() = cam_k() < steps - 1 ? smooth(clamp01((now() - cam_k() - travel) / (1 - travel))) : 0;",
        "function lerp(a, b, f) = a + (b - a) * f;",
        "$vpt = lerp(cam_t[cam_k()], cam_t[min(steps - 1, cam_k() + 1)], cam_f());",
        "$vpd = lerp(cam_d[cam_k()], cam_d[min(steps - 1, cam_k() + 1)], cam_f());",
        f"$vpr = {_vec(VIEW_ROT)};",
        "",
        "module dashed_arrow(from, to) {",
        "  d = to - from; len = norm(d);",
        "  if (len > 1) {",
        "    rz = atan2(d[1], d[0]); ry = acos(d[2] / len);",
        "    translate(from) rotate([0, ry, rz]) {",
        "      for (s = [0 : 6 : max(0, len - 12)]) translate([0, 0, s]) cylinder(r = 1.0, h = 3.5, $fn = 16);",
        "      translate([0, 0, len - 7]) cylinder(r1 = 3.0, r2 = 0, h = 7, $fn = 24);",
        "    }",
        "  }",
        "}",
        "",
    ]
    for pid, path in bodies.items():
        lines.append(f'module body_{pid.replace("-", "_")}(a = 1) color("{PART_COLOURS[pid]}", a) import("{path.resolve().as_posix()}");')
    lines.append("")
    for pid in bodies:
        k0 = first_step[pid]
        terms = [f"{_vec(s['offset'])} * (1 - prog({s['n']}))" for s in STEPS if pid in s["move"] and s["offset"] != (0, 0, 0)]
        pose = " + ".join(terms) if terms else "[0, 0, 0]"
        col = column(pid)
        name = pid.replace("-", "_")
        if col:
            ax = AXES[col]
            spin = f"rotate([0, 0, {'-turn()' if col == 'a' else 'turn()'}])"   # clockwise seen from above (the owner, 2026-10-06)
            body = f"translate([{ax[0]:g}, {ax[1]:g}, 0]) {spin} translate([{-ax[0]:g}, {-ax[1]:g}, 0]) body_{name}(alpha({k0}));"
        else:
            body = f"body_{name}(alpha({k0}));"
        lines += [f"if (present({k0})) translate({pose})", f"  {body}"]
    lines += ["", "// The travel arrows of the stills, in the frame the moving part stands in at that step."]
    for s in STEPS:
        if s.get("turn"):
            # A clockwise arc over the Handle (seen from above): turn it to test.
            ax, ay = AXES["a"]
            lines += [
                f'if (still == {s["n"]}) color("{ARROW_COLOUR}") translate([{ax:g}, {ay:g}, 128]) {{',
                "  rotate([0, 0, -100]) rotate_extrude(angle = 200, $fn = 72) translate([44, 0]) circle(r = 1.1, $fn = 12);",
                "  rotate([0, 0, -100]) translate([44, 0, 0]) rotate([0, 0, -90])",
                "    rotate([0, 90, 0]) cylinder(r1 = 3.0, r2 = 0, h = 7, $fn = 24);",
                "}",
            ]
        for key in ("arrow", "arrow_b"):
            if key not in s:
                continue
            face, entry = s[key]
            part = s["move"][-1] if key == "arrow_b" else s["move"][0]
            shift = later_displacement(s["n"], part)
            frm = _add(face, s["offset"], shift)
            to = _add(entry, shift)
            lines.append(f'if (still == {s["n"]}) color("{ARROW_COLOUR}") dashed_arrow({_vec(frm)}, {_vec(to)});')
    return "\n".join(lines) + "\n"


def run_openscad(args: Sequence[str], cwd: Optional[Path] = None) -> None:
    cmd = [str(find_openscad()), f"--imgsize={IMGSIZE}", "--projection=o", "--colorscheme=Tomorrow", *args]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600, cwd=str(cwd) if cwd else None)
    if result.returncode != 0:
        raise RuntimeError(f"openscad failed (rc={result.returncode}):\n{result.stderr[-800:]}")


def render_stills() -> List[Path]:
    for d in (STILLS, KEYFRAMES, RENDERS):
        d.mkdir(parents=True, exist_ok=True)
    out: List[Path] = []
    n = len(STEPS)
    for s in STEPS:
        k = s["n"]
        still = STILLS / f"visual-step-{k:02}.png"
        run_openscad(["-D", f"still={k}", "-o", str(still), str(SCAD)])
        out.append(still)
        # Keyframes: just after the part appears, half way along its travel, and seated.
        for tag, frac, where in (("start", 0.1, KEYFRAMES), ("moving", 0.35, RENDERS), ("seated", 0.72, KEYFRAMES)):
            t = ((k - 1) + frac) / n
            png = where / f"render-step-{k:02}-{tag}.png"
            run_openscad(["-D", f"time={t:.5f}", "-o", str(png), str(SCAD)])
            out.append(png)
            if where is RENDERS:
                parts = s["move"] or ROLLER_A + ROLLER_B + ["base", "knob", "lid", "handle"]
                register(png.stem, png, {"kind": "anim", "ids": parts,
                         "shows": f"step {k}, {s['title']}: the moving part half way along its travel to its seat"})
        print(f"step {k:2}: {still.relative_to(ROOT).as_posix()} and 3 keyframes")
    return out


def render_frames() -> List[Path]:
    """Every frame of the animation, numbered frame00000.png on, in FRAMES."""
    if FRAMES.exists():
        shutil.rmtree(FRAMES)
    FRAMES.mkdir(parents=True)
    total = FRAMES_PER_STEP * len(STEPS)
    run_openscad([f"--animate={total}", "-o", str(FRAMES / "frame.png"), str(SCAD)], cwd=FRAMES)
    frames = sorted(FRAMES.glob("frame*.png"))
    if len(frames) != total:
        raise RuntimeError(f"{len(frames)} frames rendered, expected {total}")
    return frames


def write_mp4(frames: Sequence[Path], out: Path) -> None:
    import av
    from PIL import Image

    out.parent.mkdir(parents=True, exist_ok=True)
    with av.open(str(out), mode="w") as container:
        stream = container.add_stream("libx264", rate=FPS)
        first = Image.open(frames[0]).convert("RGB")
        stream.width, stream.height = first.size
        stream.pix_fmt = "yuv420p"
        stream.options = {"crf": "20", "preset": "medium"}
        for f in frames:
            frame = av.VideoFrame.from_image(Image.open(f).convert("RGB"))
            for packet in stream.encode(frame):
                container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)


def write_gif(frames: Sequence[Path], out: Path, width: int = 640, every: int = 3) -> None:
    from PIL import Image

    images = [Image.open(f).convert("RGB") for f in frames[::every]]
    small = []
    for im in images:
        im.thumbnail((width, width), Image.LANCZOS)
        small.append(im.quantize(colors=128, dither=Image.FLOYDSTEINBERG))
    # One duration per frame: Pillow then merges identical frames (the holds)
    # into one with their durations added, so the clip keeps its timing.
    small[0].save(out, save_all=True, append_images=small[1:], duration=[int(1000 * every / FPS)] * len(small), loop=0, optimize=True)


SHORT_SECONDS = 28       # MakerWorld takes a video under 30 seconds (the owner, 2026-10-06)
SHORT_NAME = f"{STEP_NAME}_Short"
SHORT_GIF_WIDTH = 480


def short_frames(frames: Sequence[Path]) -> List[Path]:
    """The whole animation resampled to SHORT_SECONDS at FPS: every step keeps
    its share of the time, just faster."""
    n = SHORT_SECONDS * FPS
    return [frames[round(i * (len(frames) - 1) / (n - 1))] for i in range(n)]


def write_short(frames: Sequence[Path]) -> List[Path]:
    """The under-30-second MP4 and GIF of the whole build, for a listing that
    limits a video's length; both under Video_Tutorials/."""
    quick = short_frames(frames)
    mp4 = VIDEOS / f"{SHORT_NAME}.mp4"
    write_mp4(quick, mp4)
    gif = VIDEOS / f"{SHORT_NAME}.gif"
    write_gif(quick, gif, width=SHORT_GIF_WIDTH, every=2)
    return [mp4, gif]


def write_videos(frames: Sequence[Path], gif: bool) -> List[Path]:
    out: List[Path] = []
    full = VIDEOS / f"{STEP_NAME}.mp4"
    write_mp4(frames, full)
    out.append(full)
    for s in STEPS:
        k = s["n"]
        chunk = frames[(k - 1) * FRAMES_PER_STEP:k * FRAMES_PER_STEP]
        clip = VIDEOS / "steps" / f"step-{k:02}.mp4"
        write_mp4(chunk, clip)
        out.append(clip)
    if gif:
        g = ANIM / f"{STEP_NAME}.gif"
        write_gif(frames, g)
        out.append(g)
    return out


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--stills", action="store_true", help="render the step stills and keyframes")
    ap.add_argument("--video", action="store_true", help="render every frame and write the MP4s")
    ap.add_argument("--gif", action="store_true", help="with --video, also a 640 px GIF under build/animation/")
    ap.add_argument("--short", action="store_true", help=f"the {SHORT_SECONDS}-second MP4 and GIF from the rendered frames (rendering them first if they are not there)")
    ap.add_argument("--scad-only", action="store_true", help="write the OpenSCAD file and stop")
    args = ap.parse_args(argv)
    if args.short and not args.video and len(list(FRAMES.glob("frame*.png"))) == FRAMES_PER_STEP * len(STEPS):
        for v in write_short(sorted(FRAMES.glob("frame*.png"))):
            print(f"{v.relative_to(ROOT).as_posix()}: {v.stat().st_size / 1024:.0f} KB")
        return 0
    bodies = split_bodies()
    ANIM.mkdir(parents=True, exist_ok=True)
    SCAD.write_text(scad_text(bodies), encoding="utf-8", newline="\n")
    print(f"{SCAD.relative_to(ROOT).as_posix()}: {len(bodies)} bodies, {len(STEPS)} steps")
    if args.scad_only:
        return 0
    if args.stills:
        render_stills()
    if args.video or args.short:
        frames = render_frames()
        print(f"{len(frames)} frames in {FRAMES.relative_to(ROOT).as_posix()}")
        made = write_videos(frames, args.gif) if args.video else []
        if args.short:
            made += write_short(frames)
        for v in made:
            print(f"{v.relative_to(ROOT).as_posix()}: {v.stat().st_size / 1024:.0f} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
