"""Document integrity and basic repository hygiene checks.

No hardware or AI accuracy is asserted by these tests.
"""
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
FENCES = re.compile(r"(?ms)^\s*(?:\x60{3}|~{3})[^\n]*\n.*?^\s*(?:\x60{3}|~{3})\s*$")


def test_local_markdown_links_exist():
    for document in ROOT.rglob("*.md"):
        rel = document.relative_to(ROOT)
        if any(x in {".git", ".venv", "__pycache__"} for x in rel.parts):
            continue
        content = FENCES.sub("", document.read_text(encoding="utf-8"))
        for dest in MARKDOWN_LINK.findall(content):
            target = dest.strip().split(" ", 1)[0].strip("<>")
            if target.startswith(("#", "http:", "https:", "mailto:", "data:")):
                continue
            path = target.split("#", 1)[0].split("?", 1)[0]
            if path:
                assert (document.parent / path).exists(), f"{rel}: missing {path}"


def test_issue_forms_are_yaml_and_complete():
    for path in (ROOT / ".github" / "ISSUE_TEMPLATE").glob("*.yml"):
        result = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert isinstance(result, dict), path
        if path.name != "config.yml":
            assert isinstance(result.get("name"), str) and result["name"], path
            assert isinstance(result.get("body"), list), path


def test_workflow_yaml_and_permissions():
    workflows = list((ROOT / ".github" / "workflows").glob("*.yml"))
    assert workflows, "GitHub CI workflow is missing"
    for path in workflows:
        content = path.read_text(encoding="utf-8")
        parsed = yaml.safe_load(content)
        assert isinstance(parsed, dict), path
        assert "jobs" in parsed and isinstance(parsed["jobs"], dict), path
        assert "permissions:" in content, f"{path} should declare least-privilege permissions"


def test_repository_does_not_track_runtime_secrets():
    patterns = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for essential in (".venv/", ".env", "*.db", "*.joblib", "esp32/firmware/secrets.h"):
        assert essential in patterns


def test_required_material_exists():
    for target in (
        "README.md", "LICENSE", "SECURITY.md", "CONTRIBUTING.md",
        "docs/MQTT_CONTRACT.md", "docs/MAC_RUNBOOK.md",
        "docs/IMPLEMENTATION_STATUS.md", "docs/WORKFLOWS.md",
        "docs/PR_GUIDE.md", "docs/SAFETY.md",
        "tests/smoke_mqtt.py",
    ):
        assert (ROOT / target).is_file(), target
