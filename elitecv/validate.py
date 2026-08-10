from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any

from .models import WorkspaceDocuments

SCHEMA_VERSION = 1
EVIDENCE_STATUSES = {
    "sourced",
    "self_attested",
    "externally_verified",
    "unsupported",
    "conflicted",
}
REVIEW_STATUSES = {"pending", "approved", "rejected"}
DISCLOSURES = {"private", "shareable", "restricted"}
RELEASE_EVIDENCE_STATUSES = {"sourced", "self_attested", "externally_verified"}
DATE_RE = re.compile(r"^\d{4}(?:-\d{2}(?:-\d{2})?)?$")
URL_RE = re.compile(r"^https?://[^\s]+$")


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    path: str = ""
    record_id: str = ""

    def __str__(self) -> str:
        location = f" ({self.path})" if self.path else ""
        return f"{self.code}: {self.message}{location}"


@dataclass
class BulletTrace:
    bullet: dict[str, Any]
    claims: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ValidationResult:
    errors: list[ValidationIssue] = field(default_factory=list)
    warnings: list[ValidationIssue] = field(default_factory=list)
    traces: list[BulletTrace] = field(default_factory=list)
    excluded_claims: list[dict[str, Any]] = field(default_factory=list)
    selected_entries: list[dict[str, Any]] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors

    @property
    def selected_bullet_count(self) -> int:
        return len(self.traces)

    @property
    def traceability_coverage(self) -> float:
        if not self.traces:
            return 1.0
        covered = sum(1 for trace in self.traces if trace.claims)
        return covered / len(self.traces)


def _schema_issue(document_name: str, document: dict[str, Any]) -> ValidationIssue | None:
    version = document.get("schema_version")
    if version != SCHEMA_VERSION:
        return ValidationIssue(
            "schema_version",
            f"{document_name} declares schema_version={version!r}; expected {SCHEMA_VERSION}",
            document_name,
        )
    return None


def _index_records(
    records: Any,
    kind: str,
    result: ValidationResult,
) -> dict[str, dict[str, Any]]:
    if not isinstance(records, list):
        result.errors.append(
            ValidationIssue("records_type", f"{kind} must be a list", kind)
        )
        return {}
    indexed: dict[str, dict[str, Any]] = {}
    for index, record in enumerate(records):
        path = f"{kind}[{index}]"
        if not isinstance(record, dict):
            result.errors.append(
                ValidationIssue("record_type", f"{kind} record must be a mapping", path)
            )
            continue
        record_id = record.get("id")
        if not isinstance(record_id, str) or not record_id.strip():
            result.errors.append(
                ValidationIssue("missing_id", f"{kind} record needs a stable id", path)
            )
            continue
        if record_id in indexed:
            result.errors.append(
                ValidationIssue(
                    "duplicate_id",
                    f"duplicate {kind} id `{record_id}`",
                    path,
                    record_id,
                )
            )
            continue
        indexed[record_id] = record
    return indexed


def _add_release_issue(
    result: ValidationResult,
    issue: ValidationIssue,
    strict: bool,
) -> None:
    (result.errors if strict else result.warnings).append(issue)


def _claim_is_release_eligible(
    claim: dict[str, Any],
    allowed_disclosures: set[str],
) -> bool:
    return (
        claim.get("evidence_status") in RELEASE_EVIDENCE_STATUSES
        and claim.get("review_status") == "approved"
        and claim.get("disclosure") == "shareable"
        and "shareable" in allowed_disclosures
    )


def validate_documents(
    sources: dict[str, Any],
    claims: dict[str, Any],
    profile: dict[str, Any],
    variant: dict[str, Any],
    *,
    strict: bool,
) -> ValidationResult:
    result = ValidationResult()
    for name, document in (
        ("sources", sources),
        ("claims", claims),
        ("profile", profile),
        ("variant", variant),
    ):
        issue = _schema_issue(name, document)
        if issue:
            result.errors.append(issue)

    if not isinstance(variant.get("id"), str) or not variant.get("id"):
        result.errors.append(ValidationIssue("missing_variant_id", "variant needs a stable id", "variant"))
    if not isinstance(variant.get("target_role"), str) or not variant.get("target_role"):
        result.errors.append(ValidationIssue("missing_target_role", "variant needs a target_role", "variant"))
    if variant.get("page_size", "letter") not in {"letter", "a4"}:
        result.errors.append(ValidationIssue("invalid_page_size", "variant page_size must be letter or a4", "variant"))
    page_target = variant.get("page_target", 1)
    if not isinstance(page_target, int) or isinstance(page_target, bool) or page_target < 1:
        result.errors.append(ValidationIssue("invalid_page_target", "variant page_target must be a positive integer", "variant"))

    source_records = _index_records(sources.get("sources", []), "sources", result)
    claim_records = _index_records(claims.get("claims", []), "claims", result)
    profile_root = profile.get("profile")
    if not isinstance(profile_root, dict):
        result.errors.append(ValidationIssue("profile_type", "profile must be a mapping", "profile"))
        profile_root = {}
    contact = profile_root.get("contact", {}) or {}
    for link_index, link in enumerate(contact.get("links", []) or []):
        if not isinstance(link, dict) or not URL_RE.fullmatch(str(link.get("url", ""))):
            result.errors.append(
                ValidationIssue(
                    "invalid_url",
                    "profile contact links must use an http or https URL",
                    f"profile.contact.links[{link_index}]",
                )
            )
    entry_records = _index_records(profile_root.get("entries", []), "entries", result)
    bullet_records: dict[str, dict[str, Any]] = {}
    for entry_id, entry in entry_records.items():
        bullets = entry.get("bullets", [])
        if not isinstance(bullets, list):
            result.errors.append(
                ValidationIssue("bullets_type", "entry bullets must be a list", entry_id, entry_id)
            )
            continue
        for index, bullet in enumerate(bullets):
            path = f"{entry_id}.bullets[{index}]"
            if not isinstance(bullet, dict):
                result.errors.append(
                    ValidationIssue("bullet_type", "bullet must be a mapping", path, entry_id)
                )
                continue
            bullet_id = bullet.get("id")
            if not isinstance(bullet_id, str) or not bullet_id.strip():
                result.errors.append(
                    ValidationIssue("missing_id", "bullet needs a stable id", path, entry_id)
                )
                continue
            if bullet_id in bullet_records:
                result.errors.append(
                    ValidationIssue("duplicate_id", f"duplicate bullet id `{bullet_id}`", path, bullet_id)
                )
                continue
            bullet_records[bullet_id] = bullet

    for source_id, source in source_records.items():
        if source.get("confidentiality") not in {"public", "private", "restricted"}:
            result.errors.append(
                ValidationIssue(
                    "invalid_confidentiality",
                    f"source `{source_id}` has an unknown confidentiality state",
                    "sources",
                    source_id,
                )
            )

    for entry_id, entry in entry_records.items():
        for field_name in ("start_date", "end_date"):
            value = entry.get(field_name)
            if value is not None and not DATE_RE.fullmatch(str(value)):
                result.errors.append(
                    ValidationIssue(
                        "invalid_date",
                        f"entry `{entry_id}` {field_name} must use YYYY, YYYY-MM, YYYY-MM-DD, or null",
                        "profile",
                        entry_id,
                    )
                )

    for claim_id, claim in claim_records.items():
        evidence_status = claim.get("evidence_status")
        review_status = claim.get("review_status")
        disclosure = claim.get("disclosure")
        if evidence_status not in EVIDENCE_STATUSES:
            result.errors.append(
                ValidationIssue("invalid_evidence_status", f"claim `{claim_id}` has invalid evidence_status", "claims", claim_id)
            )
        if review_status not in REVIEW_STATUSES:
            result.errors.append(
                ValidationIssue("invalid_review_status", f"claim `{claim_id}` has invalid review_status", "claims", claim_id)
            )
        if disclosure not in DISCLOSURES:
            result.errors.append(
                ValidationIssue("invalid_disclosure", f"claim `{claim_id}` has invalid disclosure", "claims", claim_id)
            )
        evidence = claim.get("evidence", [])
        if not isinstance(evidence, list):
            result.errors.append(
                ValidationIssue("evidence_type", f"claim `{claim_id}` evidence must be a list", "claims", claim_id)
            )
        for evidence_index, item in enumerate(evidence if isinstance(evidence, list) else []):
            if not isinstance(item, dict):
                result.errors.append(
                    ValidationIssue("evidence_record_type", f"claim `{claim_id}` evidence must be a mapping", f"claims[{claim_id}].evidence[{evidence_index}]", claim_id)
                )
                continue
            source_id = item.get("source_id")
            if source_id not in source_records:
                result.errors.append(
                    ValidationIssue(
                        "missing_source",
                        f"claim `{claim_id}` references missing source `{source_id}`",
                        "claims",
                        claim_id,
                    )
                )

    include_entries = variant.get("include_entries", [])
    exclude_entries = set(variant.get("exclude_entries", []) or [])
    if not isinstance(include_entries, list):
        result.errors.append(ValidationIssue("include_entries_type", "include_entries must be a list", "variant"))
        include_entries = []
    if not isinstance(variant.get("sections", []), list):
        result.errors.append(ValidationIssue("sections_type", "sections must be a list", "variant"))
    selected_ids = include_entries or list(entry_records)
    for entry_id in selected_ids:
        if entry_id not in entry_records:
            result.errors.append(
                ValidationIssue("missing_entry", f"variant references missing entry `{entry_id}`", "variant", entry_id)
            )
            continue
        if entry_id not in exclude_entries:
            result.selected_entries.append(entry_records[entry_id])

    allowed_disclosures = set(variant.get("allowed_disclosures", ["shareable"]) or [])
    if not allowed_disclosures.issubset(DISCLOSURES):
        result.errors.append(ValidationIssue("invalid_allowed_disclosures", "variant has an unknown disclosure state", "variant"))
    elif strict and allowed_disclosures != {"shareable"}:
        result.errors.append(
            ValidationIssue(
                "release_disclosure_policy",
                "release builds may allow only shareable claims",
                "variant",
            )
        )

    required_claim_ids = variant.get("required_claim_ids", []) or []
    if not isinstance(required_claim_ids, list):
        result.errors.append(ValidationIssue("required_claims_type", "required_claim_ids must be a list", "variant"))
        required_claim_ids = []
    for claim_id in required_claim_ids:
        claim = claim_records.get(claim_id)
        if claim is None:
            result.errors.append(
                ValidationIssue(
                    "required_claim_missing",
                    f"variant requires missing claim `{claim_id}`",
                    "variant",
                    claim_id,
                )
            )
        elif strict and not _claim_is_release_eligible(claim, allowed_disclosures):
            result.errors.append(
                ValidationIssue(
                    "required_claim_not_release_eligible",
                    f"variant requires claim `{claim_id}` that is not release-eligible",
                    "variant",
                    claim_id,
                )
            )

    for entry in result.selected_entries:
        entry_id = entry.get("id", "")
        for bullet in entry.get("bullets", []) or []:
            if not isinstance(bullet, dict):
                continue
            bullet_id = bullet.get("id", "")
            claim_ids = bullet.get("claim_ids", [])
            if not isinstance(claim_ids, list) or not claim_ids:
                result.errors.append(
                    ValidationIssue(
                        "bullet_without_claim",
                        f"bullet `{bullet_id}` has no approved supporting claim",
                        entry_id,
                        bullet_id,
                    )
                )
                result.traces.append(BulletTrace(bullet))
                continue
            referenced_claims: list[dict[str, Any]] = []
            for claim_id in claim_ids:
                claim = claim_records.get(claim_id)
                if claim is None:
                    result.errors.append(
                        ValidationIssue(
                            "missing_claim",
                            f"bullet `{bullet_id}` references missing claim `{claim_id}`",
                            entry_id,
                            bullet_id,
                        )
                    )
                    continue
                referenced_claims.append(claim)
                if strict and not _claim_is_release_eligible(claim, allowed_disclosures):
                    _add_release_issue(
                        result,
                        ValidationIssue(
                            "claim_not_release_eligible",
                            f"bullet `{bullet_id}` references claim `{claim_id}` that is not release-eligible",
                            entry_id,
                            bullet_id,
                        ),
                        strict,
                    )
                elif not _claim_is_release_eligible(claim, allowed_disclosures):
                    result.warnings.append(
                        ValidationIssue(
                            "claim_not_release_eligible",
                            f"bullet `{bullet_id}` references claim `{claim_id}` that is not release-eligible",
                            entry_id,
                            bullet_id,
                        )
                    )
            if bullet.get("review_status") != "approved":
                _add_release_issue(
                    result,
                    ValidationIssue(
                        "bullet_not_approved",
                        f"bullet `{bullet_id}` is not approved for release",
                        entry_id,
                        bullet_id,
                    ),
                    strict,
                )
            eligible_claims = [
                claim for claim in referenced_claims if _claim_is_release_eligible(claim, allowed_disclosures)
            ]
            result.traces.append(BulletTrace(bullet, eligible_claims))

    selected_claim_ids = {
        claim_id
        for trace in result.traces
        for claim_id in trace.bullet.get("claim_ids", [])
    }
    result.excluded_claims = [
        claim for claim_id, claim in claim_records.items() if claim_id not in selected_claim_ids
    ]
    return result


def format_issues(issues: list[ValidationIssue]) -> str:
    return "\n".join(f"ERROR {issue}" for issue in issues)
