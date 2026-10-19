"""The documentation gate: ``scripts/check_docs.py`` over the READMEs and
every Markdown file under ``Documentation/`` (quick lane, standard library
only). License: GPL-3.0-or-later"""

from __future__ import annotations

from pathlib import Path

from scripts.check_docs import check_file, gate_files

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_docs_gate_reports_nothing() -> None:
    findings = []
    for path in gate_files(PROJECT_ROOT):
        findings += check_file(path)
    report = "\n".join(f.format() for f in findings)
    assert not findings, f"{len(findings)} finding(s):\n{report}"


def test_gate_rules_fire_on_a_bad_file(tmp_path: Path) -> None:
    bad = tmp_path / "bad.md"
    (tmp_path / "exists.md").write_text("# ok\n", encoding="utf-8")
    bad.write_text(
        "# One\n\n# Two\n\n#### Skipped\n\n![](missing.png)\n\n![photo of a thing](exists.md)\n\n"
        "Please [click here](exists.md) and check the console.\n\n"
        "We leverage a robust `A1_Gear_v2`.\n\n"
        "| a | b |\n|---|---|\n| " + " ".join(["word"] * 23) + " | x |\n\n"
        "This is WCAG compliant.\n\n[gone](nowhere.md)\n",
        encoding="utf-8",
    )
    rules = {f.rule for f in check_file(bad)}
    for rule in ("one-h1", "heading-level", "alt-text", "alt-text-prefix", "link-text", "console",
                 "banned-word", "retired-word", "table-cell", "compliance-claim", "broken-link"):
        assert rule in rules, f"the {rule} rule did not fire; fired: {sorted(rules)}"


def test_gate_sees_wrapped_links_and_whole_names_only(tmp_path: Path) -> None:
    """A link whose text wraps onto the next line is still checked, and an old
    part name counts only as a whole identifier, never inside a new name."""
    page = tmp_path / "page.md"
    page.write_text(
        "# Page\n\nSee [a link whose text\nwraps](nowhere.md).\n\n"
        "`Top_Gear_A`, `Handle_v2_remix` and Handle are fine.\n",
        encoding="utf-8",
    )
    findings = check_file(page)
    assert [f.line for f in findings if f.rule == "broken-link"] == [3], [f.format() for f in findings]
    assert not [f for f in findings if f.rule == "retired-word"], [f.format() for f in findings]


def test_root_links_placeholders_and_third_party_text(tmp_path: Path) -> None:
    """A link from the repository root resolves the way GitHub reads it, a
    template placeholder is not a broken link, and the words of the Makers
    Making Change boilerplate are not judged."""
    page = PROJECT_ROOT / "README.md"
    findings = check_file(page)
    assert not findings, [f.format() for f in findings]
    text = page.read_text(encoding="utf-8")
    assert "](/Build_Files/" in text and "(<MMCWebLink>)" in text and "<!-- ABOUT MMC START -->" in text


def test_old_names_allowed_only_in_the_rename_table(tmp_path: Path) -> None:
    readme = PROJECT_ROOT / "Build_Files" / "README.md"
    text = readme.read_text(encoding="utf-8")
    assert "A1_Gear_v2" in text.split("\n## File names", 1)[1], "the rename table lost A1_Gear_v2"
    assert not [f for f in check_file(readme) if f.rule == "retired-word"]
    elsewhere = tmp_path / "elsewhere.md"
    elsewhere.write_text("# Elsewhere\n\nThe part `A1_Gear_v2` is named here outside any rename table.\n", encoding="utf-8")
    assert [f.rule for f in check_file(elsewhere)] == ["retired-word"]
