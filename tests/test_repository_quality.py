"""Low-cost checks for the documented scaffold (not hardware or model tests)."""

from pathlib import Path
import re

import yaml

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")


def test_internal_markdown_links_resolve():
    """Check relative Markdown paths; fragments are not validated."""
    for document in ROOT.rglob("*.md"):
        if any(part.startswith(".") and part != ".github" for part in document.relative_to(ROOT).parts):
            continue
        if ".venv" in document.parts or ".git" in document.parts:
            continue
        text = document.read_text(encoding="utf-8")
        # Code examples should not be considered real documentation links.
        text = re.sub(r"(?ms)^\s*```[^\n]*\n.*?^\s*```\s*$", "", text)
        for dest in LINK.findall(text):
            url = dest.strip().split(" ", 1)[0].strip("<>")
            if not url or url.startswith(("#", "http:", "https:", "mailto:")):
                continue
            relative = url.split("#", 1)[0].split("?", 1)[0]
            if not relative:
                continue
            assert (document.parent / relative).exists(), f"{document}: broken link {dest}"


def test_issue_forms_are_valid_yaml():
    for path in (ROOT / ".github" / "ISSUE_TEMPLATE").glob("*.yml"):
        parsed = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert isinstance(parsed, dict), path
        if path.name != "config.yml":
            assert parsed.get("name"), path
            assert isinstance(parsed.get("body"), list), path


def test_workflow_is_valid_yaml():
    for path in (ROOT / ".github" / "workflows").glob("*.yml"):
        assert isinstance(yaml.safe_load(path.read_text(encoding="utf-8")), dict)


def test_required_contracts_exist():
    paths = [
        "README.md", ".env.example", "SECURITY.md",
        "docs/ARCHITECTURE.md", "docs/MQTT_CONTRACT.md",
        "docs/DATA_COLLECTION_PROTOCOL.md", "docs/SAFETY.md",
        "docs/TEST_PLAN.md",
    ]
    for path in paths:
        assert (ROOT / path).is_file(), path
