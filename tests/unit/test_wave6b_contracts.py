from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).parents[2]
DOCS = (
    ROOT / "README.md",
    ROOT / "AGENTS.md",
    ROOT / "docs" / "agent-workflow.md",
    ROOT / "docs" / "agent-skill.md",
    ROOT / "docs" / "troubleshooting.md",
    ROOT / "skills" / "elite-cv-builder" / "SKILL.md",
)


def test_wave6b_documents_publish_schema_v2_and_real_workflow_contracts():
    text = "\n".join(path.read_text(encoding="utf-8") for path in DOCS)
    for term in (
        "schema v2",
        "elitecv init",
        "elitecv intake",
        "intake-apply",
        "elitecv approve",
        "elitecv validate",
        "elitecv doctor --json",
        "elitecv build",
        "revisión visual",
        "elitecv release",
        "blocking",
        "recommended",
        "optional",
        "source",
        "evidencia",
        "target_role",
        "identidad",
        "ReportLab",
        "check-public",
        "garantía ATS",
    ):
        assert term.lower() in text.lower(), term

    workflow = (ROOT / "docs" / "agent-workflow.md").read_text(encoding="utf-8")
    assert "GitHub" in workflow
    assert "instal" in workflow.lower()
    assert "manual" in workflow.lower()
    assert "YAML" in workflow


def test_wave6b_evals_are_json_and_have_observable_criteria():
    path = ROOT / "skills" / "elite-cv-builder" / "evals" / "evals.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    scenarios = {item["id"]: item for item in payload["evals"]}
    expected = {
        "direct-repository-request",
        "missing-pdflatex-or-package",
        "renderer-fallback-pressure",
        "target-role-is-not-identity",
        "spanish-locale",
        "unsupported-association",
        "ats-guarantee",
    }
    assert expected <= scenarios.keys()
    for scenario in scenarios.values():
        assert scenario["prompt"]
        assert scenario["criteria"]
        assert all(isinstance(item, str) and item.strip() for item in scenario["criteria"])
