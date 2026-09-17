from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from .intake import _transactional_replace, _validate_locator, _workspace_lock


class ApprovalError(RuntimeError):
    """A stable, user-actionable approval failure."""


@dataclass(frozen=True)
class ApprovalResult:
    source_id: str
    approved_claim_ids: tuple[str, ...]
    fingerprint: str


def _approve_claims_unlocked(
    root: Path,
    source_id: str,
    reviewer: str,
    claim_ids: list[str],
    disclosure: str,
    contact_fields: list[str] | None,
) -> ApprovalResult:
    root = root.resolve()
    if not isinstance(reviewer, str) or not reviewer.strip():
        raise ApprovalError("reviewer_required")
    if not isinstance(claim_ids, list) or not claim_ids or len(set(claim_ids)) != len(claim_ids):
        raise ApprovalError("claim_ids_required")
    if disclosure not in {"private", "restricted", "shareable"}:
        raise ApprovalError("disclosure_required")
    if not isinstance(contact_fields, list) or any(field not in {"email", "phone", "location", "links"} for field in contact_fields):
        raise ApprovalError("contact_fields_required")
    data_dir = root / "data"
    sources_doc = yaml.safe_load((data_dir / "sources.yml").read_text(encoding="utf-8")) or {}
    source = next((item for item in sources_doc.get("sources", []) if item.get("id") == source_id), None)
    if source is None:
        raise ApprovalError("source_not_registered")
    claims_doc = yaml.safe_load((data_dir / "claims.yml").read_text(encoding="utf-8")) or {}
    claims = claims_doc.get("claims", [])
    selected = []
    for claim_id in claim_ids:
        claim = next((item for item in claims if item.get("id") == claim_id), None)
        if claim is None:
            raise ApprovalError("claim_not_found")
        if claim.get("evidence_status") not in {"sourced", "self_attested"}:
            raise ApprovalError("ineligible_claim")
        if claim.get("review_status") == "rejected":
            raise ApprovalError("ineligible_claim")
        if not any(item.get("source_id") == source_id for item in claim.get("evidence", [])):
            raise ApprovalError("source_mismatch")
        if any(item.get("source_id") != source_id for item in claim.get("evidence", [])):
            raise ApprovalError("source_mismatch")
        for item in claim.get("evidence", []):
            try:
                _validate_locator(item.get("locator"))
            except Exception as exc:
                raise ApprovalError("invalid_locator") from exc
        selected.append(claim)
    decision = {"source_id": source_id, "claim_ids": claim_ids, "disclosure": disclosure, "contact_fields": contact_fields, "reviewer": reviewer.strip()}
    decision_fingerprint = hashlib.sha256(json.dumps(decision, sort_keys=True).encode()).hexdigest()
    artifact_path = root / "workspace" / "intake" / f"{source_id}.json"
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    variant_id = artifact.get("variant_id")
    if not isinstance(variant_id, str):
        raise ApprovalError("intake_artifact_incomplete")
    variant_path = data_dir / "variants" / f"{variant_id}.yml"
    variant = yaml.safe_load(variant_path.read_text(encoding="utf-8")) or {}
    if not isinstance(variant, dict) or variant.get("id") != variant_id:
        raise ApprovalError("intake_artifact_incomplete")
    audit_dir = root / "workspace" / "audit"
    audit_path = audit_dir / f"approval-{decision_fingerprint}.json"
    if audit_path.exists():
        return ApprovalResult(source_id, tuple(claim_ids), source.get("fingerprint", ""))
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    selected_ids = set(claim_ids)
    for claim in claims:
        if claim.get("id") in selected_ids:
            claim.update({"review_status": "approved", "disclosure": disclosure, "reviewed_by": reviewer.strip(), "reviewed_at": now})
    variant["contact_fields"] = list(contact_fields)
    variant["required_claim_ids"] = list(claim_ids)
    variant["allowed_disclosures"] = [disclosure]
    _transactional_replace({
        data_dir / "claims.yml": yaml.safe_dump({"schema_version": 2, "claims": claims}, allow_unicode=True, sort_keys=False).encode(),
        variant_path: yaml.safe_dump(variant, allow_unicode=True, sort_keys=False).encode(),
        audit_path: json.dumps({**decision, "timestamp": now, "fingerprint": source.get("fingerprint", ""), "decision_fingerprint": decision_fingerprint}, sort_keys=True).encode(),
    })
    return ApprovalResult(source_id, tuple(claim_ids), source.get("fingerprint", ""))


def approve_claims(
    root: Path,
    source_id: str,
    reviewer: str,
    claim_ids: list[str],
    disclosure: str,
    contact_fields: list[str] | None,
) -> ApprovalResult:
    root = root.resolve()
    with _workspace_lock(root, ApprovalError):
        return _approve_claims_unlocked(
            root, source_id, reviewer, claim_ids, disclosure, contact_fields
        )
