#!/usr/bin/env python3
"""Capture the OpenSCAD window showing the Version 2 cylinder generator.

OpenSCAD has no headless way to picture its own Customizer panel, so this
opens the real program on this computer's desktop, maximises its window,
presses F5 so the Customizer fills with the file's dials, and captures
the window (only the window: nothing else on the desktop is in the
picture). The captures go to ``build/screens/openscad-window-N.png`` (one per
scroll position of the Customizer) and their sizes are printed; scripts/openscad_guide_screenshots.py crops and marks
it for the OpenSCAD Generator Guide.

Usage:
    python scripts/openscad_gui_capture.py             # capture and close OpenSCAD
    python scripts/openscad_gui_capture.py --keep      # leave the window open
    python scripts/openscad_gui_capture.py --keys F5   # keys to press before the capture (comma-separated)

Local lane, Windows only: needs the OpenSCAD 2026.01.03 nightly at its
usual path, an unlocked desktop and Pillow. License: GPL-3.0-or-later
"""

from __future__ import annotations

import argparse
import ctypes
import ctypes.wintypes as wt
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

from PIL import ImageGrab

ROOT = Path(__file__).resolve().parent.parent
OPENSCAD_GUI = Path(r"C:\Program Files\OpenSCAD (Nightly)\openscad.exe")
SCAD = ROOT / "Build_Files" / "3D_Printing_Files" / "Embossing_Plates_Customizer" / "OpenSCAD_Offline_Alternative" / "Braille_Cylinder_STL_Generator_EmbosserV2.scad"
OUT = ROOT / "build" / "screens" / "openscad-window.png"
TITLE_PART = "OpenSCAD"
SW_MAXIMIZE = 3
VK = {"F5": 0x74, "F6": 0x75, "ESC": 0x1B, "ENTER": 0x0D, "TAB": 0x09}

user32 = ctypes.windll.user32
dwmapi = ctypes.windll.dwmapi


def find_window(title_part: str, timeout_s: float = 60) -> int:
    """The handle of the top-level window whose title holds ``title_part``."""
    found = []
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wt.HWND, wt.LPARAM)

    def cb(hwnd, _lparam):
        if user32.IsWindowVisible(hwnd):
            n = user32.GetWindowTextLengthW(hwnd)
            if n:
                buf = ctypes.create_unicode_buffer(n + 1)
                user32.GetWindowTextW(hwnd, buf, n + 1)
                if title_part in buf.value and SCAD.name in buf.value:
                    found.append(hwnd)
        return True

    deadline = time.time() + timeout_s
    while time.time() < deadline:
        found.clear()
        user32.EnumWindows(WNDENUMPROC(cb), 0)
        if found:
            return found[0]
        time.sleep(1)
    raise RuntimeError("no OpenSCAD window with the generator open")


def window_rect(hwnd: int) -> tuple:
    """The window's frame without the invisible resize border (DWM's extended frame)."""
    rect = wt.RECT()
    DWMWA_EXTENDED_FRAME_BOUNDS = 9
    if dwmapi.DwmGetWindowAttribute(wt.HWND(hwnd), ctypes.c_uint(DWMWA_EXTENDED_FRAME_BOUNDS), ctypes.byref(rect), ctypes.sizeof(rect)) != 0:
        user32.GetWindowRect(wt.HWND(hwnd), ctypes.byref(rect))
    return (rect.left, rect.top, rect.right, rect.bottom)


def press(key: str) -> None:
    code = VK[key.upper()]
    user32.keybd_event(code, 0, 0, 0)
    time.sleep(0.05)
    user32.keybd_event(code, 0, 2, 0)


def take_focus(hwnd: int, x: int, y: int) -> None:
    """Click inside OpenSCAD's window so it holds the keyboard before any key
    is pressed. Windows may refuse SetForegroundWindow to a background script,
    and a key pressed then lands in whatever window is in front (on 2026-10-07
    an F5 reached another program that way), while a click always brings its
    window forward. Stops, having clicked nothing, if another window covers
    the point; stops, having pressed nothing, if OpenSCAD still lacks the
    focus."""
    user32.WindowFromPoint.argtypes = [wt.POINT]
    user32.WindowFromPoint.restype = wt.HWND
    user32.GetAncestor.restype = wt.HWND
    user32.GetForegroundWindow.restype = wt.HWND
    under = user32.WindowFromPoint(wt.POINT(x, y))
    GA_ROOT = 2
    root = user32.GetAncestor(under, GA_ROOT) if under else None
    if root != hwnd:
        cls = ctypes.create_unicode_buffer(256)
        if root:
            user32.GetClassNameW(root, cls, 256)
        what = "the lock screen: unlock the computer" if cls.value.startswith("LockScreen") else f"window class {cls.value!r}"
        raise RuntimeError(f"another window covers OpenSCAD's window ({what}); nothing was clicked or pressed")
    user32.SetCursorPos(x, y)
    time.sleep(0.2)
    MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP = 0x0002, 0x0004
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    time.sleep(0.5)
    if user32.GetForegroundWindow() != hwnd:
        raise RuntimeError("OpenSCAD did not take the keyboard focus; no key was pressed")


def keep_on_top(hwnd: int, on: bool) -> None:
    """Hold the window above every other while it is captured, and let go
    after. The capture reads the screen, so a window in front would be in
    the picture, and a background script may not bring a window forward any
    other way; on 2026-10-07 the owner's window stayed in front of OpenSCAD."""
    HWND_TOPMOST, HWND_NOTOPMOST = -1, -2
    SWP_NOSIZE, SWP_NOMOVE, SWP_SHOWWINDOW = 0x0001, 0x0002, 0x0040
    user32.SetWindowPos.argtypes = [wt.HWND, wt.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint]
    user32.SetWindowPos(hwnd, HWND_TOPMOST if on else HWND_NOTOPMOST, 0, 0, 0, 0,
                        SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW)


def wheel(x: int, y: int, notches: int) -> None:
    """Scroll with the mouse wheel over a point of the window (negative notches scroll down)."""
    user32.SetCursorPos(x, y)
    time.sleep(0.2)
    MOUSEEVENTF_WHEEL = 0x0800
    user32.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, notches * 120, 0)
    time.sleep(0.8)


def capture(keys: Sequence[str], settle_s: float, keep: bool, scrolls: Sequence[int] = (0,),
            wheel_at: Tuple[int, int] = (1720, 600), click_at: Tuple[int, int] = (700, 960)) -> List[Path]:
    """One capture per entry of ``scrolls``: each entry is how many wheel
    notches to scroll the Customizer (down for negative) before that capture.
    ``click_at`` is a point in the Console, where a click changes nothing."""
    proc = subprocess.Popen([str(OPENSCAD_GUI), str(SCAD)])
    outs: List[Path] = []
    hwnd = None
    try:
        hwnd = find_window(TITLE_PART)
        time.sleep(3)
        user32.ShowWindow(hwnd, SW_MAXIMIZE)
        keep_on_top(hwnd, True)
        user32.SetForegroundWindow(hwnd)
        time.sleep(2)
        box = window_rect(hwnd)
        if keys:
            take_focus(hwnd, box[0] + click_at[0], box[1] + click_at[1])
        for key in keys:
            press(key)
            time.sleep(1)
        time.sleep(settle_s)
        box = window_rect(hwnd)
        OUT.parent.mkdir(parents=True, exist_ok=True)
        for i, notches in enumerate(scrolls, 1):
            user32.SetForegroundWindow(hwnd)
            time.sleep(0.5)
            if notches:
                wheel(box[0] + wheel_at[0], box[1] + wheel_at[1], notches)
                time.sleep(1.0)
            im = ImageGrab.grab(bbox=box)
            out = OUT.with_name(f"{OUT.stem}-{i}.png")
            im.save(out)
            outs.append(out)
            print(f"{out.relative_to(ROOT).as_posix()} {im.width}x{im.height} from window {box}, scrolled {notches}")
        return outs
    finally:
        if hwnd:
            keep_on_top(hwnd, False)
        if not keep:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--keys", default="F5", help="keys to press before the capture, comma-separated (default F5)")
    ap.add_argument("--settle", type=float, default=25.0, help="seconds to wait after the keys (the preview takes a while)")
    ap.add_argument("--keep", action="store_true", help="leave OpenSCAD open")
    ap.add_argument("--scrolls", default="0", help="wheel notches before each capture, comma-separated (default one capture, no scroll)")
    args = ap.parse_args(argv)
    capture([k for k in args.keys.split(",") if k], args.settle, args.keep, [int(s) for s in args.scrolls.split(",")])
    return 0


if __name__ == "__main__":
    sys.exit(main())
