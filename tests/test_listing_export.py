"""The plain-Markdown copy of the listing's description stays what the listing gives (quick lane)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXPORT = PROJECT_ROOT / "Documentation" / "Custom_Braille_Embosser_V2_Listing_Description.md"


def test_listing_description_export_is_current() -> None:
    result = subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts" / "listing_description_markdown.py"), "--check"],
                            capture_output=True, text=True, cwd=str(PROJECT_ROOT))
    assert result.returncode == 0, result.stdout + result.stderr
    text = EXPORT.read_text(encoding="utf-8")
    assert "![" not in text, "the sites take pictures in their gallery, not in the description"
    assert "MakerWorld allows one license" not in text
