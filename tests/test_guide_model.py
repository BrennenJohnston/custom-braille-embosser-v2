"""``scripts/guide_model.py``: the guide read as steps (quick lane,
standard library only). License: GPL-3.0-or-later"""

from __future__ import annotations

from pathlib import Path

from scripts.guide_model import GUIDE, load, parse

FIXTURE = """# A guide

One paragraph.

## 1. Before

Prose.

## 4. Assemble

### Roller A

### Step 1: Stand the part up

You need the part.

**Careful: this goes one way.** Really.

1. Hold it.
2. Stand it up.

**Check:** It stands.

**By touch:** Feel the top.

![The part standing.](../Photos/stages/x.jpg)

The part stands on the mat.

<!-- shot: part-close | angle: low, hands | show: the top face -->

### Step 2: Nothing yet

1. Wait.
"""


def test_fixture_parses_into_steps() -> None:
    g = parse(FIXTURE)
    assert g.title == "A guide"
    assert [s.title for s in g.sections] == ["1. Before", "4. Assemble"]
    steps = g.steps
    assert [s.number for s in steps] == [1, 2]
    one = steps[0]
    assert one.lines == ["Hold it.", "Stand it up."]
    assert one.check == "It stands."
    assert one.by_touch == "Feel the top."
    assert one.careful.startswith("**Careful:")
    assert one.you_need == "You need the part."
    assert one.pictures[0].alt == "The part standing." and one.pictures[0].caption == "The part stands on the mat."
    assert one.shots[0].name == "part-close" and one.shots[0].angle == "low, hands"
    assert one.has_picture
    assert not steps[1].has_picture and not steps[1].by_touch


def test_the_guide_keeps_its_contract() -> None:
    """Every step has at least one picture or a shot request, a Check and
    a By touch block, and no two steps share their action text."""
    if not GUIDE.exists():
        return
    g = load()
    assert g.steps, "the guide has no steps"
    numbers = [s.number for s in g.steps]
    assert numbers == list(range(1, len(numbers) + 1)), f"step numbers are not 1..n: {numbers}"
    problems = []
    for s in g.steps:
        if not s.has_picture:
            problems.append(f"Step {s.number} has no picture and no shot request")
        if not s.check:
            problems.append(f"Step {s.number} has no Check")
        if not s.by_touch:
            problems.append(f"Step {s.number} has no By touch")
        if not s.lines:
            problems.append(f"Step {s.number} has no numbered actions")
    assert not problems, "\n".join(problems)
    texts = [" ".join(s.lines) for s in g.steps]
    assert len(texts) == len(set(texts)), "two steps have the same actions (the Version 1 Step 9 defect)"
    for s in g.steps:
        for p in s.pictures:
            assert p.alt and len(p.alt) <= 150, f"Step {s.number}: alt text missing or over 150 characters"
            assert p.caption, f"Step {s.number}: {Path(p.path).name} has no caption paragraph"
