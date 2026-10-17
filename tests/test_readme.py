"""Regression checks to keep the README current and links working."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"


def test_readme_has_no_person_by_person_assignment():
    readme = README.read_text(encoding="utf-8")
    prohibited = (
        "Team Responsibilities and Contributors",
        "Responsibility Overview",
        "| Team member | GitHub | Primary responsibilities |",
    )
    for phrase in prohibited:
        assert phrase not in readme


def test_readme_relative_markdown_links_exist():
    text = README.read_text(encoding="utf-8")
    for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
        if target.startswith(("https://", "http://", "#", "mailto:")):
            continue
        path = target.split("#", 1)[0]
        assert (ROOT / path).exists(), f"README points to missing path: {path}"


def test_runbook_points_to_main_and_safe_pull():
    runbook = (ROOT / "docs" / "MAC_RUNBOOK.md").read_text(encoding="utf-8")
    assert "git pull --ff-only origin main" in runbook
    assert "git switch -c feature/full-stack-mvp-2026-10" not in runbook
