from __future__ import annotations

import json
from pathlib import Path

import pytest

from elitecv.approval import ApprovalError, approve_claims
from elitecv.cli import _init, main
from elitecv.intake import IntakeError, apply_intake_proposal, intake_source
from elitecv.models import load_yaml
from elitecv.validate import validate_documents


def _proposal(source_id: str, *, status: str = "sourced", evidence_source: str | None = None) -> dict:
    evidence_source = evidence_source or source_id
    return {
        "schema_version": 2,
        "source_id": source_id,
        "fingerprint": "not-used-by-fixture",
        "profile": {
            "schema_version": 2,
            "profile": {
                "id": "profile.synthetic",
                "name": "Synthetic Candidate",
                "headline": "Data Engineer",
                "headline_claim_ids": ["claim.synthetic"],
                "contact": {"email": None, "phone": None, "location": None, "links": []},
                "entries": [],
                "skill_groups": [],
            },
        },
        "claims": [{
            "id": "claim.synthetic",
            "statement": "Built a synthetic data pipeline.",
            "evidence": [{"source_id": evidence_source, "locator": "section:control"}],
            "evidence_status": status,
            "review_status": "pending",
            "disclosure": "private",
            "reviewed_by": None,
            "reviewed_at": None,
            "questions": [],
        }],
        "questions": [
            {"id": "q-metric", "text": "Confirm the measured outcome.", "priority": "recommended"},
            {"id": "q-identity", "text": "Confirm identity.", "priority": "blocking"},
            {"id": "q-link", "text": "Add an optional link.", "priority": "optional"},
        ],
    }


def _registered_workspace(tmp_path: Path) -> tuple[str, str]:
    _init(tmp_path, "General", "letter")
    source = tmp_path / "resume.md"
    source.write_text("Synthetic source", encoding="utf-8")
    result = intake_source(tmp_path, source, "Data Engineer", "en-US", "denied")
    return result.source_id, result.fingerprint


def test_apply_proposal_writes_private_documents_and_prioritized_questions(tmp_path):
    source_id, fingerprint = _registered_workspace(tmp_path)
    proposal = _proposal(source_id)
    proposal["fingerprint"] = fingerprint
    proposal_path = tmp_path / "proposal.json"
    proposal_path.write_text(json.dumps(proposal), encoding="utf-8")

    apply_intake_proposal(tmp_path, source_id, proposal_path)

    assert load_yaml(tmp_path / "data" / "claims.yml")["claims"][0]["review_status"] == "pending"
    assert load_yaml(tmp_path / "data" / "profile.yml")["profile"]["headline"] == "Data Engineer"
    artifact = json.loads((tmp_path / "workspace" / "intake" / f"{source_id}.json").read_text())
    assert artifact["mapping_status"] == "proposed"
    question_record = json.loads((tmp_path / "workspace" / "review" / f"{source_id}-questions.json").read_text())
    assert question_record["source_id"] == source_id
    assert [item["priority"] for item in question_record["questions"]] == [
        "blocking",
        "recommended",
        "optional",
    ]
    assert "Synthetic source" not in json.dumps(question_record)


def test_apply_rejects_source_mismatch_and_approved_sourced_claim(tmp_path):
    source_id, fingerprint = _registered_workspace(tmp_path)
    proposal = _proposal(source_id, evidence_source="source-other")
    proposal["fingerprint"] = fingerprint
    with pytest.raises(IntakeError, match="source_mismatch"):
        apply_intake_proposal(tmp_path, source_id, proposal)

    proposal = _proposal(source_id)
    proposal["fingerprint"] = fingerprint
    proposal["claims"][0]["review_status"] = "approved"
    with pytest.raises(IntakeError, match="sourced_claim_must_be_pending"):
        apply_intake_proposal(tmp_path, source_id, proposal)


def test_apply_rejects_unsupported_or_conflicted_presented_as_approved(tmp_path):
    source_id, fingerprint = _registered_workspace(tmp_path)
    for status in ("unsupported", "conflicted"):
        proposal = _proposal(source_id, status=status)
        proposal["fingerprint"] = fingerprint
        proposal["claims"][0]["review_status"] = "approved"
        with pytest.raises(IntakeError, match="ineligible_claim_approval"):
            apply_intake_proposal(tmp_path, source_id, proposal)


def test_approval_is_explicit_selective_private_and_idempotent(tmp_path):
    source_id, fingerprint = _registered_workspace(tmp_path)
    proposal = _proposal(source_id)
    proposal["fingerprint"] = fingerprint
    apply_intake_proposal(tmp_path, source_id, proposal)

    result = approve_claims(tmp_path, source_id, "owner", ["claim.synthetic"], "shareable", ["email"])
    assert result.approved_claim_ids == ("claim.synthetic",)
    claims = load_yaml(tmp_path / "data" / "claims.yml")["claims"]
    assert claims[0]["review_status"] == "approved"
    variant = load_yaml(tmp_path / "data" / "variants" / "data-engineer.yml")
    assert variant["contact_fields"] == ["email"]
    audits = list((tmp_path / "workspace" / "audit").glob("*.json"))
    assert len(audits) == 1
    audit = json.loads(audits[0].read_text())
    assert audit["claim_ids"] == ["claim.synthetic"]
    assert audit["fingerprint"]
    approve_claims(tmp_path, source_id, "owner", ["claim.synthetic"], "shareable", ["email"])
    assert len(list((tmp_path / "workspace" / "audit").glob("*.json"))) == 1


def test_approval_rejects_omitted_or_unsupported_claims_and_requires_disclosures(tmp_path):
    source_id, fingerprint = _registered_workspace(tmp_path)
    proposal = _proposal(source_id)
    proposal["fingerprint"] = fingerprint
    proposal["claims"].append({**proposal["claims"][0], "id": "claim.other", "evidence_status": "unsupported", "evidence": []})
    apply_intake_proposal(tmp_path, source_id, proposal)
    with pytest.raises(ApprovalError, match="claim_ids"):
        approve_claims(tmp_path, source_id, "owner", [], "shareable", ["email"])
    with pytest.raises(ApprovalError, match="ineligible_claim"):
        approve_claims(tmp_path, source_id, "owner", ["claim.other"], "shareable", ["email"])
    with pytest.raises(ApprovalError, match="contact_fields"):
        approve_claims(tmp_path, source_id, "owner", ["claim.synthetic"], "shareable", None)

    claims_path = tmp_path / "data" / "claims.yml"
    claims_doc = load_yaml(claims_path)
    claims_doc["claims"][0]["review_status"] = "rejected"
    claims_path.write_text(__import__("yaml").safe_dump(claims_doc, sort_keys=False), encoding="utf-8")
    with pytest.raises(ApprovalError, match="ineligible_claim"):
        approve_claims(tmp_path, source_id, "owner", ["claim.synthetic"], "shareable", [])


def test_approval_allows_validate_and_build_ready_state(tmp_path):
    source_id, fingerprint = _registered_workspace(tmp_path)
    proposal = _proposal(source_id)
    proposal["fingerprint"] = fingerprint
    apply_intake_proposal(tmp_path, source_id, proposal)
    approve_claims(tmp_path, source_id, "owner", ["claim.synthetic"], "shareable", [])
    documents = __import__("elitecv.models", fromlist=["load_workspace"]).load_workspace(tmp_path, "data-engineer")
    result = validate_documents(documents.sources, documents.claims, documents.profile, documents.variant, strict=False)
    assert result.errors == []


def test_cli_exposes_concise_wave4b_commands(tmp_path, capsys):
    source_id, fingerprint = _registered_workspace(tmp_path)
    proposal = _proposal(source_id)
    proposal["fingerprint"] = fingerprint
    path = tmp_path / "proposal.json"
    path.write_text(json.dumps(proposal), encoding="utf-8")
    assert main(["intake-apply", "--root", str(tmp_path), "--source-id", source_id, "--proposal", str(path)]) == 0
    assert main(["approve", "--root", str(tmp_path), "--source-id", source_id, "--reviewer", "owner", "--claim-id", "claim.synthetic", "--disclosure", "shareable", "--contact-field", "email"]) == 0
    assert "Synthetic source" not in capsys.readouterr().out
