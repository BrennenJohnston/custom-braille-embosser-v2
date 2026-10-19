"""``scripts/shot_list.py``: the shot list is what the guide asks for
(quick lane, standard library only). License: GPL-3.0-or-later"""

from __future__ import annotations

from scripts.guide_model import GUIDE, load, parse
from scripts.shot_list import NO_PICTURE, OUT, page, rows_for

FIXTURE = """# G

P.

## 2. Parts

<!-- shot: parts-row | angle: top | show: the four gears pegs up -->

## 4. Assemble

### Step 1: With picture

1. Do.

**Check:** Done.

**By touch:** Felt.

![Alt.](../Photos/stages/a.jpg)

Caption.

### Step 2: With shot only

1. Do.

**Check:** Done.

**By touch:** Felt.

<!-- shot: step-two | angle: low, hands | show: the peg entering -->

### Step 3: Nothing

1. Do.

**Check:** Done.

**By touch:** Felt.
"""


def test_rows_come_from_shots_and_bare_steps() -> None:
    rows = rows_for(parse(FIXTURE))
    assert rows[0] == ["2. Parts", "parts-row", "top", "the four gears pegs up"]
    assert rows[1] == ["Step 2", "step-two", "low, hands", "the peg entering"]
    assert rows[2][:2] == ["Step 3", NO_PICTURE]
    assert len(rows) == 3
    text = page(parse(FIXTURE))
    assert text.startswith("# Shot list") and "| Step 2 | step-two |" in text


def test_shot_list_on_disk_is_current() -> None:
    """The list is a working file under build/; one that has been written is what the guide asks for now."""
    if not GUIDE.exists() or not OUT.exists():
        return
    assert OUT.read_text(encoding="utf-8").replace("\r\n", "\n") == page(load()), "the shot list is stale; run scripts/shot_list.py"
