from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any

from .models import WorkspaceDocuments

SCHEMA_VERSION = 2
EVIDENCE_STATUSES = {
    "sourced",
    "self_attested",
    "externally_verified",
    "unsupported",
    "conflicted",
}
REVIEW_STATUSES = {"pending", "approved", "rejected"}
DISCLOSURES = {"private", "shareable", "restricted"}
SUPPORTED_LOCALES = {"en-US", "es-MX"}
RELEASE_EVIDENCE_STATUSES = {"sourced", "self_attested", "externally_verified"}
DATE_RE = re.compile(r"^\d{4}(?:-\d{2}(?:-\d{2})?)?$")
URL_RE = re.compile(r"^https?://[^\s]+$")
SAFE_LOCATOR_RE = re.compile(
    r"^(?:page:[1-9]\d{0,3}|line:[1-9]\d{0,3}|"
    r"section:[a-z0-9]+(?:-[a-z0-9]+)*)$"
)


def is_safe_locator(value: Any) -> bool:
    if not isinstance(value, str) or len(value) > 80:
        return False
    match = SAFE_LOCATOR_RE.fullmatch(value)
    return match is not None


def _shape_error(result: ValidationResult, code: str, message: str, path: str) -> None:
    result.errors.append(ValidationIssue(code, message, path))


def _check_mapping_shape(
    value: Any,
    *,
    required: set[str],
    allowed: set[str],
    path: str,
    result: ValidationResult,
) -> bool:
    if not isinstance(value, dict):
        _shape_error(result, "field_type", "value must be a mapping", path)
        return False
    for key in required - value.keys():
        _shape_error(result, "missing_field", f"required field `{key}` is missing", f"{path}.{key}")
    for key in value.keys() - allowed:
        _shape_error(result, "additional_property", f"unknown field `{key}`", f"{path}.{key}")
    return True


def _check_string(value: Any, path: str, result: ValidationResult, *, nullable: bool = False) -> None:
    if nullable and value is None:
        return
    if not isinstance(value, str) or not value.strip():
        _shape_error(result, "field_type", "value must be a non-empty string", path)


def _check_string_list(value: Any, path: str, result: ValidationResult) -> None:
    if not isinstance(value, list):
        _shape_error(result, "field_type", "value must be a list", path)
        return
    for index, item in enumerate(value):
        _check_string(item, f"{path}[{index}]", result)


def _validate_sources_shape(sources: Any, result: ValidationResult) -> None:
    if not _check_mapping_shape(
        sources,
        required={"schema_version", "sources"},
        allowed={"schema_version", "sources"},
        path="sources_document",
        result=result,
    ):
        return
    records = sources.get("sources")
    if not isinstance(records, list):
        _shape_error(result, "field_type", "sources must be a list", "sources")
        return
    fields = {"id", "type", "label", "path", "confidentiality", "collected_at", "fingerprint"}
    for index, source in enumerate(records):
        path = f"sources[{index}]"
        if not _check_mapping_shape(source, required=fields, allowed=fields, path=path, result=result):
            continue
        for field_name in ("id", "type", "label", "path", "confidentiality", "collected_at"):
            _check_string(source.get(field_name), f"{path}.{field_name}", result)
        _check_string(source.get("fingerprint"), f"{path}.fingerprint", result, nullable=True)
        collected_at = source.get("collected_at")
        if isinstance(collected_at, str) and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", collected_at):
            _shape_error(result, "invalid_date", "collected_at must use YYYY-MM-DD", f"{path}.collected_at")


def _validate_claims_shape(claims: Any, result: ValidationResult) -> None:
    if not _check_mapping_shape(
        claims,
        required={"schema_version", "claims"},
        allowed={"schema_version", "claims"},
        path="claims_document",
        result=result,
    ):
        return
    records = claims.get("claims")
    if not isinstance(records, list):
        _shape_error(result, "field_type", "claims must be a list", "claims")
        return
    required = {"id", "statement", "evidence", "evidence_status", "review_status", "disclosure"}
    allowed = required | {"reviewed_by", "reviewed_at", "questions"}
    for index, claim in enumerate(records):
        path = f"claims[{index}]"
        if not _check_mapping_shape(claim, required=required, allowed=allowed, path=path, result=result):
            continue
        for field_name in ("id", "statement", "evidence_status", "review_status", "disclosure"):
            _check_string(claim.get(field_name), f"{path}.{field_name}", result)
        for field_name in ("reviewed_by", "reviewed_at"):
            if field_name in claim:
                _check_string(claim.get(field_name), f"{path}.{field_name}", result, nullable=True)
        if "questions" in claim:
            _check_string_list(claim.get("questions"), f"{path}.questions", result)
        evidence = claim.get("evidence")
        if not isinstance(evidence, list):
            _shape_error(result, "field_type", "evidence must be a list", f"{path}.evidence")
            continue
        for evidence_index, item in enumerate(evidence):
            item_path = f"{path}.evidence[{evidence_index}]"
            if not _check_mapping_shape(
                item,
                required={"source_id", "locator"},
                allowed={"source_id", "locator", "excerpt"},
                path=item_path,
                result=result,
            ):
                continue
            _check_string(item.get("source_id"), f"{item_path}.source_id", result)
            if not is_safe_locator(item.get("locator")):
                _shape_error(result, "invalid_locator", "locator must be a safe structured reference", f"{item_path}.locator")
            if "excerpt" in item and item.get("excerpt") is not None and not isinstance(item.get("excerpt"), str):
                _shape_error(result, "field_type", "excerpt must be a string or null", f"{item_path}.excerpt")


def _validate_profile_shape(profile: Any, result: ValidationResult) -> None:
    if not _check_mapping_shape(profile, required={"schema_version", "profile"}, allowed={"schema_version", "profile"}, path="profile_document", result=result):
        return
    root = profile.get("profile")
    if not _check_mapping_shape(root, required={"id", "name", "headline", "headline_claim_ids", "contact", "entries", "skill_groups"}, allowed={"id", "name", "headline", "headline_claim_ids", "contact", "entries", "skill_groups"}, path="profile", result=result):
        return
    for field in ("id", "name", "headline"):
        _check_string(root.get(field), f"profile.{field}", result)
    _check_string_list(root.get("headline_claim_ids"), "profile.headline_claim_ids", result)
    contact = root.get("contact")
    if _check_mapping_shape(contact, required={"email", "phone", "location", "links"}, allowed={"email", "phone", "location", "links"}, path="profile.contact", result=result):
        for field in ("email", "phone", "location"):
            _check_string(contact.get(field), f"profile.contact.{field}", result, nullable=True)
        links = contact.get("links")
        if not isinstance(links, list):
            _shape_error(result, "field_type", "value must be a list", "profile.contact.links")
        else:
            for index, link in enumerate(links):
                if _check_mapping_shape(link, required={"label", "url"}, allowed={"label", "url"}, path=f"profile.contact.links[{index}]", result=result):
                    _check_string(link.get("label"), f"profile.contact.links[{index}].label", result)
                    _check_string(link.get("url"), f"profile.contact.links[{index}].url", result)
    entries = root.get("entries")
    if not isinstance(entries, list):
        _shape_error(result, "field_type", "value must be a list", "profile.entries")
    else:
        entry_allowed = {"id", "section", "organization", "role", "location", "start_date", "end_date", "date_precision", "claim_ids", "bullets"}
        for index, entry in enumerate(entries):
            path = f"profile.entries[{index}]"
            if not _check_mapping_shape(entry, required=entry_allowed, allowed=entry_allowed, path=path, result=result):
                continue
            for field in ("id", "section", "organization", "role"):
                _check_string(entry.get(field), f"{path}.{field}", result)
            for field in ("location", "start_date", "end_date"):
                _check_string(entry.get(field), f"{path}.{field}", result, nullable=True)
            if entry.get("date_precision") not in {"year", "month", "day"}:
                _shape_error(result, "invalid_date_precision", "date_precision must be year, month, or day", f"{path}.date_precision")
            precision = entry.get("date_precision")
            for field in ("start_date", "end_date"):
                value = entry.get(field)
                if value is not None and isinstance(value, str) and not re.fullmatch({"year": r"\d{4}", "month": r"\d{4}-\d{2}", "day": r"\d{4}-\d{2}-\d{2}"}.get(precision, r"$^"), value):
                    _shape_error(result, "date_precision_mismatch", f"{field} does not match date_precision", f"{path}.{field}")
            _check_string_list(entry.get("claim_ids"), f"{path}.claim_ids", result)
            bullets = entry.get("bullets")
            if not isinstance(bullets, list):
                _shape_error(result, "field_type", "value must be a list", f"{path}.bullets")
            else:
                for bullet_index, bullet in enumerate(bullets):
                    bullet_path = f"{path}.bullets[{bullet_index}]"
                    if _check_mapping_shape(bullet, required={"id", "text", "claim_ids", "review_status"}, allowed={"id", "text", "claim_ids", "review_status"}, path=bullet_path, result=result):
                        _check_string(bullet.get("id"), f"{bullet_path}.id", result)
                        _check_string(bullet.get("text"), f"{bullet_path}.text", result)
                        _check_string_list(bullet.get("claim_ids"), f"{bullet_path}.claim_ids", result)
                        if bullet.get("review_status") not in REVIEW_STATUSES:
                            _shape_error(result, "invalid_review_status", "invalid review_status", f"{bullet_path}.review_status")
    groups = root.get("skill_groups")
    if not isinstance(groups, list):
        _shape_error(result, "field_type", "value must be a list", "profile.skill_groups")
    else:
        for index, group in enumerate(groups):
            path = f"profile.skill_groups[{index}]"
            if not _check_mapping_shape(group, required={"id", "label", "items"}, allowed={"id", "label", "items"}, path=path, result=result):
                continue
            _check_string(group.get("id"), f"{path}.id", result)
            _check_string(group.get("label"), f"{path}.label", result)
            items = group.get("items")
            if not isinstance(items, list):
                _shape_error(result, "field_type", "value must be a list", f"{path}.items")
            else:
                for item_index, item in enumerate(items):
                    item_path = f"{path}.items[{item_index}]"
                    if _check_mapping_shape(item, required={"name", "claim_ids"}, allowed={"name", "claim_ids"}, path=item_path, result=result):
                        _check_string(item.get("name"), f"{item_path}.name", result)
                        _check_string_list(item.get("claim_ids"), f"{item_path}.claim_ids", result)


def _validate_variant_shape(variant: Any, result: ValidationResult) -> None:
    allowed = {"schema_version", "id", "target_role", "locale", "page_size", "density", "page_target", "sections", "include_entries", "include_skill_groups", "contact_fields", "exclude_entries", "required_claim_ids", "allowed_disclosures"}
    required = {"schema_version", "id", "target_role", "sections", "include_entries", "include_skill_groups", "contact_fields"}
    if not _check_mapping_shape(variant, required=required, allowed=allowed, path="variant", result=result):
        return
    _check_string(variant.get("id"), "variant.id", result)
    _check_string(variant.get("target_role"), "variant.target_role", result)
    if "locale" in variant:
        _check_string(variant["locale"], "variant.locale", result)
    if "page_target" in variant and (not isinstance(variant["page_target"], int) or isinstance(variant["page_target"], bool)):
        _shape_error(result, "field_type", "page_target must be an integer", "variant.page_target")
    for field in ("sections", "include_entries", "include_skill_groups", "contact_fields", "exclude_entries", "required_claim_ids", "allowed_disclosures"):
        if field in variant:
            _check_string_list(variant[field], f"variant.{field}", result)


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
    structured_provenance: list[dict[str, Any]] = field(default_factory=list)
    disclosure_checks: list[dict[str, Any]] = field(default_factory=list)

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
    version = document.get("schema_version") if isinstance(document, dict) else None
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


def _claim_refs(
    result: ValidationResult,
    claim_records: dict[str, dict[str, Any]],
    claim_ids: Any,
    path: str,
    allowed_disclosures: set[str],
    strict: bool,
) -> list[dict[str, Any]]:
    if not isinstance(claim_ids, list) or not claim_ids:
        result.errors.append(ValidationIssue("structured_without_claim", "visible structured field needs claim_ids", path))
        return []
    referenced: list[dict[str, Any]] = []
    eligible_ids: list[str] = []
    for claim_id in claim_ids:
        claim = claim_records.get(claim_id)
        if claim is None:
            result.errors.append(ValidationIssue("missing_claim", f"structured field references missing claim `{claim_id}`", path, claim_id))
            continue
        referenced.append(claim)
        if _claim_is_release_eligible(claim, allowed_disclosures):
            eligible_ids.append(claim_id)
        else:
            _add_release_issue(
                result,
                ValidationIssue("structured_claim_not_release_eligible", f"structured field at `{path}` references claim `{claim_id}` that is not release-eligible", path, claim_id),
                strict,
            )
    result.structured_provenance.append({"path": path, "claim_ids": list(claim_ids), "eligible": bool(eligible_ids)})
    return referenced


def validate_documents(
    sources: dict[str, Any],
    claims: dict[str, Any],
    profile: dict[str, Any],
    variant: dict[str, Any],
    *,
    strict: bool,
) -> ValidationResult:
    result = ValidationResult()
    _validate_sources_shape(sources, result)
    _validate_claims_shape(claims, result)
    _validate_profile_shape(profile, result)
    _validate_variant_shape(variant, result)
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
    if variant.get("locale", "en-US") not in SUPPORTED_LOCALES:
        result.errors.append(ValidationIssue("unsupported_locale", "variant locale must be en-US or es-MX", "variant"))
    if variant.get("page_size", "letter") not in {"letter", "a4"}:
        result.errors.append(ValidationIssue("invalid_page_size", "variant page_size must be letter or a4", "variant"))
    if variant.get("density", "medium") not in {"short", "medium", "dense"}:
        result.errors.append(ValidationIssue("invalid_density", "variant density must be short, medium, or dense", "variant"))
    page_target = variant.get("page_target", 1)
    if not isinstance(page_target, int) or isinstance(page_target, bool) or page_target < 1:
        result.errors.append(ValidationIssue("invalid_page_target", "variant page_target must be a positive integer", "variant"))

    source_records = _index_records(sources.get("sources", []), "sources", result)
    claim_records = _index_records(claims.get("claims", []), "claims", result)
    profile_root = profile.get("profile") if isinstance(profile, dict) else None
    if not isinstance(profile_root, dict):
        result.errors.append(ValidationIssue("profile_type", "profile must be a mapping", "profile"))
        profile_root = {}
    contact = profile_root.get("contact", {}) or {}
    if not isinstance(contact, dict):
        result.errors.append(ValidationIssue("contact_type", "profile contact must be a mapping", "profile.contact"))
        contact = {}
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
    skill_groups = profile_root.get("skill_groups", [])
    if not isinstance(skill_groups, list):
        result.errors.append(ValidationIssue("skill_groups_type", "skill_groups must be a list", "profile"))
        skill_groups = []
    skill_group_records = _index_records(skill_groups, "skill_groups", result)
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
            if not is_safe_locator(item.get("locator")):
                result.errors.append(
                    ValidationIssue(
                        "invalid_locator",
                        f"claim `{claim_id}` uses an unsafe evidence locator",
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

    contact_fields = variant.get("contact_fields", [])
    allowed_contact_fields = {"email", "phone", "location", "links"}
    if not isinstance(contact_fields, list):
        result.errors.append(ValidationIssue("contact_fields_type", "contact_fields must be a list", "variant"))
        contact_fields = []
    for field_name in contact_fields:
        allowed = field_name in allowed_contact_fields
        result.disclosure_checks.append({"field": field_name, "allowed": allowed})
        if not allowed:
            result.errors.append(ValidationIssue("invalid_contact_field", f"variant contact_fields contains unknown field `{field_name}`", "variant", str(field_name)))

    _claim_refs(result, claim_records, profile_root.get("headline_claim_ids"), "profile.headline", allowed_disclosures, strict)
    for entry in result.selected_entries:
        entry_id = entry.get("id", "")
        _claim_refs(result, claim_records, entry.get("claim_ids"), f"profile.entries[{entry_id}].metadata", allowed_disclosures, strict)

    include_skill_groups = variant.get("include_skill_groups", [])
    if not isinstance(include_skill_groups, list):
        result.errors.append(ValidationIssue("include_skill_groups_type", "include_skill_groups must be a list", "variant"))
        include_skill_groups = []
    selected_group_ids = include_skill_groups or list(skill_group_records)
    for group_id in selected_group_ids:
        group = skill_group_records.get(group_id)
        if group is None:
            result.errors.append(ValidationIssue("missing_skill_group", f"variant references missing skill group `{group_id}`", "variant", str(group_id)))
            continue
        items = group.get("items", [])
        if not isinstance(items, list):
            result.errors.append(ValidationIssue("skill_items_type", f"skill group `{group_id}` items must be a list", "profile", group_id))
            continue
        for index, item in enumerate(items):
            path = f"profile.skill_groups[{group_id}].items[{index}]"
            if not isinstance(item, dict):
                result.errors.append(ValidationIssue("skill_item_type", "skill item must be a mapping", path, group_id))
                continue
            refs = _claim_refs(result, claim_records, item.get("claim_ids"), path, allowed_disclosures, strict)
            if not refs:
                result.errors.append(ValidationIssue("skill_without_claim", f"skill `{item.get('name', '')}` has no supporting claim", path, group_id))

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
