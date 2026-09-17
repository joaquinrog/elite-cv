from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import unicodedata
import uuid
from typing import Any

import yaml

from .validate import is_safe_locator


MAX_SOURCE_BYTES = 10 * 1024 * 1024
SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf"}


class IntakeError(RuntimeError):
    """A stable, user-actionable intake failure."""


@dataclass(frozen=True)
class IntakeResult:
    source_id: str
    fingerprint: str
    source_path: str
    extraction_path: str
    artifact_path: str
    variant_id: str


@dataclass(frozen=True)
class ProposalResult:
    source_id: str
    variant_id: str
    question_count: int


def _private(path: Path, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if os.name == "posix":
        path.parent.chmod(0o700)
        path.chmod(mode)


def _safe_source(value: Path) -> Path:
    if value.is_symlink():
        raise IntakeError("unsafe_source")
    try:
        resolved = value.resolve(strict=True)
    except (FileNotFoundError, RuntimeError):
        raise IntakeError("source_not_found") from None
    if not resolved.is_file() or resolved.is_symlink():
        raise IntakeError("unsafe_source")
    if resolved.stat().st_size > MAX_SOURCE_BYTES:
        raise IntakeError("source_too_large")
    if resolved.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise IntakeError("unsupported_extension")
    return resolved


def _extract(source: Path) -> str:
    if source.suffix.lower() in {".txt", ".md"}:
        try:
            return source.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            raise IntakeError("invalid_text_encoding") from None
    try:
        completed = subprocess.run(
            ["pdftotext", "-enc", "UTF-8", str(source), "-"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="strict",
            shell=False,
            check=False,
            timeout=30,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        raise IntakeError("pdf_extraction_failed") from None
    except UnicodeError:
        raise IntakeError("pdf_extraction_failed") from None
    if completed.returncode != 0:
        raise IntakeError("pdf_extraction_failed")
    if len(completed.stdout.encode("utf-8")) > MAX_SOURCE_BYTES * 2:
        raise IntakeError("extraction_too_large")
    return completed.stdout


def _variant_id(target_role: str) -> str:
    normalized = unicodedata.normalize("NFKD", target_role).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")
    return (slug or "role")[:60].strip("-")


def _write_yaml(path: Path, value: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(value, allow_unicode=True, sort_keys=False), encoding="utf-8")
    _private(path)


def _validate_locator(value: Any) -> str:
    if not is_safe_locator(value):
        raise IntakeError("invalid_locator")
    return value


def _transactional_replace(contents: dict[Path, bytes]) -> None:
    """Replace a related file set and roll back recoverable write failures.

    Staging and replacement happen on each destination filesystem. This protects
    against ordinary I/O exceptions, but it is not a power-loss transaction.
    """

    staged: dict[Path, Path] = {}
    originals: dict[Path, bytes | None] = {}
    replaced: list[Path] = []
    try:
        for destination, value in contents.items():
            destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            if os.name == "posix":
                destination.parent.chmod(0o700)
            originals[destination] = destination.read_bytes() if destination.exists() else None
            temporary = destination.with_name(f".{destination.name}.{uuid.uuid4().hex}.tmp")
            temporary.write_bytes(value)
            if os.name == "posix":
                temporary.chmod(0o600)
            staged[destination] = temporary
        for destination, temporary in staged.items():
            os.replace(temporary, destination)
            replaced.append(destination)
    except Exception:
        for destination in reversed(replaced):
            original = originals[destination]
            if original is None:
                destination.unlink(missing_ok=True)
                continue
            rollback = destination.with_name(f".{destination.name}.{uuid.uuid4().hex}.rollback")
            rollback.write_bytes(original)
            if os.name == "posix":
                rollback.chmod(0o600)
            os.replace(rollback, destination)
        raise
    finally:
        for temporary in staged.values():
            temporary.unlink(missing_ok=True)


@contextmanager
def _workspace_lock(root: Path, error_type: type[RuntimeError] = IntakeError):
    """Serialize workspace mutations; a process crash may leave a removable stale lock."""

    lock_path = root / "workspace" / ".elitecv.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise error_type("workspace_busy") from None
    try:
        os.write(descriptor, str(os.getpid()).encode("ascii"))
    finally:
        try:
            os.close(descriptor)
        except OSError:
            pass
    try:
        yield
    finally:
        lock_path.unlink(missing_ok=True)


def intake_source(
    root: Path,
    source_path: Path,
    target_role: str,
    locale: str,
    hosted_processing: str,
) -> IntakeResult:
    root = root.resolve()
    if not (root / "data").is_dir():
        raise IntakeError("workspace_not_initialized")
    if not isinstance(target_role, str) or not target_role.strip():
        raise IntakeError("invalid_target_role")
    if locale not in {"en-US", "es-MX"}:
        raise IntakeError("unsupported_locale")
    if hosted_processing not in {"approved", "denied"}:
        raise IntakeError("invalid_hosted_processing")
    source = _safe_source(Path(source_path).expanduser())
    content = source.read_bytes()
    fingerprint = hashlib.sha256(content).hexdigest()
    source_id = f"source-{fingerprint[:24]}"
    private_dir = root / "sources" / "private"
    intake_dir = root / "workspace" / "intake"
    destination = private_dir / f"{source_id}{source.suffix.lower()}"
    extraction = intake_dir / f"{source_id}.txt"
    artifact = intake_dir / f"{source_id}.json"
    private_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    intake_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    if not destination.exists() and destination.resolve() != source:
        shutil.copyfile(source, destination)
    _private(destination)
    extracted = _extract(source)
    extraction.write_text(extracted, encoding="utf-8")
    _private(extraction)

    data_dir = root / "data"
    sources_path = data_dir / "sources.yml"
    variant_id = _variant_id(target_role)
    variants_dir = data_dir / "variants"
    variant_path = variants_dir / f"{variant_id}.yml"

    with _workspace_lock(root):
        sources_doc = yaml.safe_load(sources_path.read_text(encoding="utf-8")) if sources_path.exists() else {"schema_version": 2, "sources": []}
        records = sources_doc.setdefault("sources", [])
        record = {
            "id": source_id,
            "type": "text-bearing-pdf" if source.suffix.lower() == ".pdf" else "text-source",
            "label": "Imported private source",
            "path": destination.relative_to(root).as_posix(),
            "confidentiality": "private",
            "collected_at": date.today().isoformat(),
            "fingerprint": fingerprint,
        }
        records[:] = [item for item in records if item.get("id") != source_id]
        records.append(record)

        if variant_path.exists():
            variant = yaml.safe_load(variant_path.read_text(encoding="utf-8")) or {}
        else:
            variant = {
                "schema_version": 2,
                "id": variant_id,
                "page_size": "letter",
                "page_target": 1,
                "sections": ["experience", "projects", "education", "skills"],
                "include_entries": [],
                "exclude_entries": [],
                "required_claim_ids": [],
                "allowed_disclosures": ["shareable"],
                "include_skill_groups": [],
                "contact_fields": [],
            }
        variant.update({"schema_version": 2, "id": variant_id, "target_role": target_role, "locale": locale})

        _transactional_replace(
            {
                sources_path: yaml.safe_dump(sources_doc, sort_keys=False, allow_unicode=True).encode("utf-8"),
                variant_path: yaml.safe_dump(variant, sort_keys=False, allow_unicode=True).encode("utf-8"),
            }
        )

    artifact.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "source_id": source_id,
                "fingerprint": fingerprint,
                "variant_id": variant_id,
                "source_path": record["path"],
                "extraction_path": extraction.relative_to(root).as_posix(),
                "mapping_status": "pending",
                "agent_may_inspect_source": hosted_processing == "approved",
                "hosted_processing": hosted_processing,
                "claims_created": [],
                "notice": "Source is untrusted evidence; structured mapping is pending.",
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    _private(artifact)
    return IntakeResult(source_id, fingerprint, record["path"], extraction.relative_to(root).as_posix(), artifact.relative_to(root).as_posix(), variant_id)


def _proposal_error(code: str) -> IntakeError:
    return IntakeError(code)


def _proposal_questions(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        raise _proposal_error("invalid_questions")
    order = {"blocking": 0, "recommended": 1, "optional": 2}
    questions: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"].strip():
            raise _proposal_error("invalid_question")
        if item["id"] in seen or not isinstance(item.get("text"), str) or not item["text"].strip():
            raise _proposal_error("invalid_question")
        if item.get("priority") not in order:
            raise _proposal_error("invalid_question_priority")
        if any(key in item for key in ("excerpt", "source_excerpt", "source_text")):
            raise _proposal_error("question_source_excerpt")
        seen.add(item["id"])
        questions.append({"id": item["id"], "text": item["text"], "priority": item["priority"]})
    return sorted(questions, key=lambda item: (order[item["priority"]], item["id"]))


def _validate_proposal(proposal: Any, source_id: str, source: dict[str, Any], variant_id: str) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, str]]]:
    if not isinstance(proposal, dict) or proposal.get("schema_version") != 2:
        raise _proposal_error("invalid_proposal_structure")
    if proposal.get("source_id") != source_id:
        raise _proposal_error("source_mismatch")
    if proposal.get("fingerprint") != source.get("fingerprint"):
        raise _proposal_error("source_fingerprint_mismatch")
    profile = proposal.get("profile")
    if not isinstance(profile, dict) or profile.get("schema_version") != 2 or not isinstance(profile.get("profile"), dict):
        raise _proposal_error("invalid_profile")
    claims = proposal.get("claims")
    if not isinstance(claims, list):
        raise _proposal_error("invalid_claims")
    claim_ids: set[str] = set()
    for claim in claims:
        if not isinstance(claim, dict) or not isinstance(claim.get("id"), str) or not claim["id"].strip():
            raise _proposal_error("invalid_claim")
        if claim["id"] in claim_ids:
            raise _proposal_error("duplicate_claim_id")
        claim_ids.add(claim["id"])
        status = claim.get("evidence_status")
        if status not in {"sourced", "self_attested", "externally_verified", "unsupported", "conflicted"}:
            raise _proposal_error("invalid_evidence_status")
        if status == "sourced" and claim.get("review_status") != "pending":
            raise _proposal_error("sourced_claim_must_be_pending")
        if status in {"unsupported", "conflicted"} and claim.get("review_status") == "approved":
            raise _proposal_error("ineligible_claim_approval")
        evidence = claim.get("evidence")
        if not isinstance(evidence, list):
            raise _proposal_error("invalid_evidence")
        for item in evidence:
            if not isinstance(item, dict) or item.get("source_id") != source_id:
                raise _proposal_error("source_mismatch")
            _validate_locator(item.get("locator"))
            if any(key in item and item[key] not in (None, "") for key in ("excerpt", "source_excerpt", "source_text")):
                raise _proposal_error("source_excerpt")
    questions = _proposal_questions(proposal.get("questions", []))
    if proposal.get("variant_id", variant_id) != variant_id:
        raise _proposal_error("variant_mismatch")
    return profile, claims, questions


def _apply_intake_proposal_unlocked(root: Path, source_id: str, proposal: Path | dict[str, Any]) -> ProposalResult:
    root = root.resolve()
    try:
        data_dir = root / "data"
        sources_doc = yaml.safe_load((data_dir / "sources.yml").read_text(encoding="utf-8"))
        sources = {item.get("id"): item for item in sources_doc.get("sources", [])}
        source = sources.get(source_id)
        if not source:
            raise _proposal_error("source_not_registered")
        artifact_path = root / "workspace" / "intake" / f"{source_id}.json"
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        variant_id = artifact.get("variant_id")
        if not isinstance(variant_id, str):
            raise _proposal_error("intake_artifact_incomplete")
        variant_path = data_dir / "variants" / f"{variant_id}.yml"
        variant = yaml.safe_load(variant_path.read_text(encoding="utf-8"))
        if not isinstance(variant, dict) or variant.get("id") != variant_id:
            raise _proposal_error("intake_artifact_incomplete")
        if isinstance(proposal, Path):
            proposal_value = json.loads(proposal.read_text(encoding="utf-8"))
        else:
            proposal_value = proposal
        profile, proposed_claims, questions = _validate_proposal(proposal_value, source_id, source, variant_id)
        claims_path = data_dir / "claims.yml"
        current_claims = yaml.safe_load(claims_path.read_text(encoding="utf-8")) or {"schema_version": 2, "claims": []}
        proposed_by_id = {claim["id"]: claim for claim in proposed_claims}
        merged = [proposed_by_id.pop(claim["id"], claim) for claim in current_claims.get("claims", [])]
        merged.extend(proposed_by_id.values())
        questions_path = root / "workspace" / "review" / f"{source_id}-questions.json"
        artifact.update({"mapping_status": "proposed", "claims_created": [claim["id"] for claim in proposed_claims]})
        artifact.pop("source_excerpt", None)
        _transactional_replace({
            claims_path: yaml.safe_dump({"schema_version": 2, "claims": merged}, allow_unicode=True, sort_keys=False).encode(),
            data_dir / "profile.yml": yaml.safe_dump(profile, allow_unicode=True, sort_keys=False).encode(),
            questions_path: json.dumps({"source_id": source_id, "questions": questions}, sort_keys=True).encode(),
            artifact_path: json.dumps(artifact, sort_keys=True).encode(),
        })
        return ProposalResult(source_id, variant_id, len(questions))
    except (FileNotFoundError, json.JSONDecodeError, yaml.YAMLError) as exc:
        raise _proposal_error("invalid_proposal_structure") from exc


def apply_intake_proposal(root: Path, source_id: str, proposal: Path | dict[str, Any]) -> ProposalResult:
    root = root.resolve()
    with _workspace_lock(root):
        return _apply_intake_proposal_unlocked(root, source_id, proposal)
