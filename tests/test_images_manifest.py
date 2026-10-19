"""``Documentation/images.json`` against ``Photos/`` and the guide (quick
lane, standard library only). With ``RELEASE_CHECK=1`` in the environment
the lane also refuses any picture the guide uses whose description the owner
has not reviewed. License: GPL-3.0-or-later"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = PROJECT_ROOT / "Documentation" / "images.json"
PHOTOS = PROJECT_ROOT / "Photos"
GUIDES = sorted((PROJECT_ROOT / "Documentation").glob("*Custom_Braille_Embosser_V2_*.md"))
LEAD = "Braille_Embosser_V2.jpg"
NAME = re.compile(r"^(overview|part|stage|finished|render|frame|visual|screen)-[a-z0-9-]+\.(jpg|png)$")
CAMERA_NAME = re.compile(r"\d{8}_\d{6}")
IMAGE_LINE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)\)")
USES = {"guide", "spare", "reject", "undecided"}
ALT_STATUS = {"none", "draft", "reviewed"}
KINDS = {"photo", "frame", "render"}


def records() -> list:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def photo_files() -> list:
    return sorted(p for p in PHOTOS.rglob("*") if p.is_file() and p.name != LEAD)


def guide_images() -> list:
    """The pictures the guides show from Photos/; a GIF shown from Video_Tutorials/ is a video, not a registered picture."""
    text = "\n".join(g.read_text(encoding="utf-8") for g in GUIDES)
    return [Path(m.group(1)).name for m in IMAGE_LINE.finditer(text) if "/Photos/" in m.group(1)]


def test_records_are_well_formed() -> None:
    recs = records()
    assert recs, "the registry is empty"
    names = [r["name"] for r in recs if r["name"]]
    assert len(names) == len(set(names)), "two records share a name"
    # A photo or render is its own source; frames share a video, so a frame's
    # identity is the video plus its time.
    sources = [(r["origin"]["source"], r["origin"].get("time")) for r in recs]
    assert len(sources) == len(set(sources)), "two records share a source"
    for r in recs:
        if r["origin"]["kind"] == "frame":
            assert re.match(r"^\d+:\d\d(\.\d+)?$", r["origin"]["time"]), f"{r['name']} has no m:ss time"
    for r in recs:
        assert r["use"] in USES, r
        assert r["alt_status"] in ALT_STATUS, r
        assert r["origin"]["kind"] in KINDS, r
        if r["name"]:
            assert NAME.match(r["name"]), f"{r['name']} does not follow the naming pattern"
            assert r["name"].split("-", 1)[0] in ("overview", "part", "stage", "finished", "render", "frame", "visual", "screen")
        if r["use"] == "guide":
            assert r["name"] and r["shows"] and r["subject"], f"a chosen photo is not described: {r['origin']['source']}"


def test_every_file_under_photos_is_registered_and_named_for_people() -> None:
    by_name = {r["name"]: r for r in records() if r["name"]}
    for path in photo_files():
        assert not CAMERA_NAME.search(path.name), f"{path.name} still carries a camera name"
        assert path.name in by_name, f"{path.relative_to(PROJECT_ROOT).as_posix()} has no registry record"
        assert path.parent.name == by_name[path.name]["group"], f"{path.name} is in the wrong group folder"


def test_every_chosen_photo_that_was_imported_is_on_disk_unchanged() -> None:
    import hashlib
    for r in records():
        if r["use"] != "guide":
            continue
        digest = r["origin"].get("imported_sha256")
        if digest is None:
            continue
        path = PHOTOS / r["group"] / r["name"]
        assert path.exists(), f"{r['name']} was imported but is missing"
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, f"{r['name']} changed since import"


def test_every_picture_the_guide_uses_is_registered() -> None:
    by_name = {r["name"]: r for r in records() if r["name"]}
    for name in guide_images():
        assert name in by_name, f"the guide shows {name}, which the registry does not know"
        assert by_name[name]["use"] == "guide", f"the guide shows {name}, which is marked {by_name[name]['use']}"
        assert (PHOTOS / by_name[name]["group"] / name).exists(), f"the guide shows {name}, which is not in Photos/"


def test_release_needs_every_used_picture_reviewed() -> None:
    if os.environ.get("RELEASE_CHECK") != "1":
        return
    by_name = {r["name"]: r for r in records() if r["name"]}
    unreviewed = [n for n in guide_images() if by_name[n]["alt_status"] != "reviewed"]
    assert not unreviewed, f"pictures the guide uses whose descriptions are not reviewed: {unreviewed}"
