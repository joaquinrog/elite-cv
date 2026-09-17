from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any

from . import __version__
from .diagnostics import check_dependencies, required_dependency_failures
from .locale import format_date_range, get_locale
from .models import WorkspaceDocuments, WorkspaceError, load_workspace
from .pdf_audit import audit_pdf_text
from .render import render_latex
from .report import render_audit_report, render_evidence_report
from .validate import ValidationResult, format_issues, validate_documents


class BuildError(RuntimeError):
    """Raised when a deterministic build cannot produce a valid artifact."""


COMMAND_TIMEOUT_SECONDS = 60


@dataclass(frozen=True)
class BuildResult:
    target: str
    output_dir: Path
    pdf_path: Path
    preview_path: Path
    evidence_report_path: Path
    audit_report_path: Path
    manifest_path: Path
    extracted_text_path: Path
    page_count: int
    validation: ValidationResult


def _run(command: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            cwd=cwd,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=COMMAND_TIMEOUT_SECONDS,
        )
    except FileNotFoundError as exc:
        raise BuildError(
            f"Missing tool `{command[0]}`. Run `elitecv doctor` for installation guidance."
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise BuildError(
            f"Command timed out after {COMMAND_TIMEOUT_SECONDS} seconds: {' '.join(command)}"
        ) from exc
    except subprocess.CalledProcessError as exc:
        tail = "\n".join(exc.stdout.splitlines()[-12:]) if exc.stdout else "no tool output"
        raise BuildError(f"Command failed: {' '.join(command)}\n{tail}") from exc


def _tool_version(command: str) -> str:
    version_args = {
        "pdftotext": ["-v"],
        "pdftoppm": ["-v"],
        "pdfinfo": ["-v"],
    }.get(command, ["--version"])
    try:
        result = subprocess.run(
            [command, *version_args],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "missing"
    first_line = (result.stdout or "").splitlines()
    return first_line[0][:160] if first_line else "unknown"


def _compile_pdf(build_dir: Path) -> Path:
    tex_path = build_dir / "cv.tex"
    pdf_path = build_dir / "cv.pdf"
    if shutil.which("latexmk"):
        try:
            _run(
                [
                    "latexmk",
                    "-pdf",
                    "-interaction=nonstopmode",
                    "-halt-on-error",
                    "-outdir=.",
                    "-pdflatex=pdflatex -no-shell-escape %O %S",
                    tex_path.name,
                ],
                cwd=build_dir,
            )
        except BuildError:
            if not shutil.which("pdflatex"):
                raise
            pdf_path.unlink(missing_ok=True)
    if not pdf_path.is_file():
        if not shutil.which("pdflatex"):
            raise BuildError(
                "No LaTeX compiler found. Install TeX Live or MiKTeX with pdflatex; then run `elitecv doctor`."
            )
        _run(["pdflatex", "-no-shell-escape", "-interaction=nonstopmode", "-halt-on-error", tex_path.name], cwd=build_dir)
        _run(["pdflatex", "-no-shell-escape", "-interaction=nonstopmode", "-halt-on-error", tex_path.name], cwd=build_dir)
    if not pdf_path.is_file():
        raise BuildError(f"LaTeX completed without producing {pdf_path}")
    return pdf_path


def _page_count(pdf_path: Path) -> int:
    if not shutil.which("pdfinfo"):
        raise BuildError("Missing tool `pdfinfo`. Install Poppler and run `elitecv doctor`.")
    result = _run(["pdfinfo", str(pdf_path)], cwd=pdf_path.parent)
    for line in result.stdout.splitlines():
        if line.startswith("Pages:"):
            return int(line.split(":", 1)[1].strip())
    raise BuildError(f"Could not read page count from {pdf_path}")


def _safe_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _input_hashes(documents: WorkspaceDocuments) -> dict[str, str]:
    paths = [
        documents.data_dir / "sources.yml",
        documents.data_dir / "claims.yml",
        documents.data_dir / "profile.yml",
        documents.variant_path,
    ]
    return {path.relative_to(documents.root).as_posix(): _safe_hash(path) for path in paths}


def _tools_used() -> dict[str, str]:
    return {
        name: _tool_version(name)
        for name in ("python3", "latexmk", "pdflatex", "pdftotext", "pdftoppm", "pdfinfo")
    }


def _private_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    if os.name == "posix":
        path.chmod(0o700)


def _restrict_private_tree(root: Path) -> None:
    if os.name != "posix":
        return
    root.chmod(0o700)
    for path in root.rglob("*"):
        path.chmod(0o700 if path.is_dir() else 0o600)


def _protected_pdf_fields(
    profile: dict[str, Any], variant: dict[str, Any], entries: list[dict[str, Any]],
) -> dict[str, str]:
    protected_fields = {"headline": str(profile.get("headline", ""))}
    for entry in entries:
        entry_id = str(entry.get("id", "entry"))
        for field_name in ("role", "title", "organization"):
            value = entry.get(field_name)
            if value:
                protected_fields[f"{entry_id}.{field_name}"] = str(value)
    groups = {
        str(group.get("id")): group
        for group in profile.get("skill_groups", []) or []
        if isinstance(group, dict)
    }
    for group_id in variant.get("include_skill_groups", []) or []:
        group = groups.get(str(group_id))
        if not group:
            continue
        for index, item in enumerate(group.get("items", []) or []):
            if isinstance(item, dict) and item.get("name"):
                protected_fields[f"{group_id}.items[{index}]"] = str(item["name"])
    return protected_fields


def _expected_pdf_fields(
    profile: dict[str, Any], variant: dict[str, Any], entries: list[dict[str, Any]],
) -> dict[str, str]:
    locale = get_locale(str(variant.get("locale", "en-US")))
    expected = {
        "name": str(profile.get("name", "")),
        "headline": str(profile.get("headline", "")),
    }
    entries_by_section: dict[str, list[dict[str, Any]]] = {}
    for entry in entries:
        entries_by_section.setdefault(str(entry.get("section", "experience")), []).append(entry)
        entry_id = str(entry.get("id", "entry"))
        for field_name in ("role", "title", "organization", "location"):
            value = entry.get(field_name)
            if value:
                expected[f"{entry_id}.{field_name}"] = str(value)
        expected[f"{entry_id}.dates"] = format_date_range(
            entry.get("start_date"), entry.get("end_date"), locale.code
        )

    groups = {
        str(group.get("id")): group
        for group in profile.get("skill_groups", []) or []
        if isinstance(group, dict)
    }
    for section in variant.get("sections", []) or []:
        if section == "skills":
            selected_groups = [
                groups[group_id]
                for group_id in variant.get("include_skill_groups", []) or []
                if group_id in groups
            ]
            if selected_groups:
                expected["section.skills"] = locale.section("skills")
            for group in selected_groups:
                group_id = str(group.get("id", "skills"))
                expected[f"{group_id}.label"] = str(group.get("label", ""))
                for index, item in enumerate(group.get("items", []) or []):
                    if isinstance(item, dict) and item.get("name"):
                        expected[f"{group_id}.items[{index}]"] = str(item["name"])
        elif entries_by_section.get(str(section)):
            expected[f"section.{section}"] = locale.section(str(section))

    contact = profile.get("contact", {}) or {}
    for field_name in variant.get("contact_fields", []) or []:
        if field_name in {"email", "phone", "location"} and contact.get(field_name):
            expected[f"contact.{field_name}"] = str(contact[field_name])
        elif field_name == "links":
            for index, link in enumerate(contact.get("links", []) or []):
                if isinstance(link, dict) and (link.get("label") or link.get("url")):
                    expected[f"contact.links[{index}]"] = str(link.get("label") or link["url"])
    return {key: value for key, value in expected.items() if value}


def build_variant(
    root: Path,
    target: str,
    *,
    output_dir: Path | None = None,
    strict: bool = True,
) -> BuildResult:
    try:
        documents = load_workspace(root, target)
    except WorkspaceError as exc:
        raise BuildError(str(exc)) from exc
    validation = validate_documents(
        documents.sources,
        documents.claims,
        documents.profile,
        documents.variant,
        strict=strict,
    )
    if not validation.is_valid:
        raise BuildError(format_issues(validation.errors))
    if validation.traceability_coverage != 1.0:
        raise BuildError(
            f"Bullet traceability coverage is {validation.traceability_coverage:.0%}; every rendered bullet needs an eligible claim."
        )

    dependency_failures = required_dependency_failures(check_dependencies())
    if dependency_failures:
        details = "; ".join(
            f"{check.check_id}: {check.remediation}" for check in dependency_failures
        )
        raise BuildError(f"Missing renderer dependencies: {details}")

    output_base = (output_dir or (documents.root / "dist")).resolve()
    target_dir = (output_base / target).resolve()
    try:
        target_dir.relative_to(output_base)
    except ValueError as exc:
        raise BuildError(f"Target `{target}` resolves outside {output_base}") from exc
    if target_dir.exists():
        shutil.rmtree(target_dir)
    share_dir = target_dir / "share"
    private_dir = target_dir / "private"
    build_dir = private_dir / "build"
    _private_directory(target_dir)
    _private_directory(share_dir)
    _private_directory(private_dir)
    _private_directory(build_dir)

    tex_path = build_dir / "cv.tex"
    tex_path.write_text(render_latex(documents, validation), encoding="utf-8")
    built_pdf = _compile_pdf(build_dir)
    pdf_path = share_dir / "cv.pdf"
    shutil.copy2(built_pdf, pdf_path)

    extracted_text_path = build_dir / "cv.txt"
    _run(["pdftotext", "-layout", str(pdf_path), str(extracted_text_path)], cwd=build_dir)
    preview_prefix = build_dir / "preview"
    _run(["pdftoppm", "-png", "-singlefile", "-r", "150", str(pdf_path), str(preview_prefix)], cwd=build_dir)
    preview_path = share_dir / "preview.png"
    shutil.copy2(build_dir / "preview.png", preview_path)
    page_count = _page_count(pdf_path)
    extracted_text = extracted_text_path.read_text(encoding="utf-8")
    profile = documents.profile["profile"]
    expected_fields = _expected_pdf_fields(
        profile, documents.variant, validation.selected_entries
    )
    protected_fields = _protected_pdf_fields(profile, documents.variant, validation.selected_entries)
    pdf_text_quality = audit_pdf_text(
        extracted_text,
        expected_fields=expected_fields,
        protected_fields=protected_fields,
    )
    if pdf_text_quality["status"] != "pass":
        codes = ", ".join(str(item["code"]) for item in pdf_text_quality["findings"])
        raise BuildError(f"PDF text quality audit failed: {codes}")
    expected_pages = documents.variant.get("page_target")
    if isinstance(expected_pages, int) and page_count != expected_pages:
        raise BuildError(
            f"Variant `{target}` targets {expected_pages} page(s), but the PDF has {page_count}."
        )

    evidence_report_path = private_dir / "evidence-report.html"
    evidence_report_path.write_text(
        render_evidence_report(
            documents,
            validation,
            page_count=page_count,
            tool_version=f"elitecv {__version__}",
        ),
        encoding="utf-8",
    )
    audit_report_path = private_dir / "audit-report.md"
    audit_report_path.write_text(
        render_audit_report(
            documents,
            validation,
            page_count=page_count,
            extracted_text_path=extracted_text_path.relative_to(target_dir).as_posix(),
        ),
        encoding="utf-8",
    )
    manifest_path = private_dir / "build-manifest.json"
    manifest: dict[str, Any] = {
        "elitecv_version": __version__,
        "schema_version": documents.variant.get("schema_version"),
        "variant_id": documents.variant.get("id"),
        "target_role": documents.variant.get("target_role"),
        "input_hashes": _input_hashes(documents),
        "built_at": datetime.now(timezone.utc).isoformat(),
        "tools": _tools_used(),
        "page_count": page_count,
        "traceability_coverage": validation.traceability_coverage,
        "traceability_scope": "selected_bullets",
        "bullet_traceability": {
            "coverage": validation.traceability_coverage,
            "scope": "selected_bullets",
            "status": "not applicable" if validation.selected_bullet_count == 0 else "measured",
        },
        "structured_field_provenance": validation.structured_provenance,
        "disclosure_checks": validation.disclosure_checks,
        "pdf_text_quality": pdf_text_quality,
        "checks": {
            "schema": not any(issue.code == "schema_version" for issue in validation.errors),
            "bullet_traceability": validation.traceability_coverage == 1.0,
            "structured_field_provenance": all(
                bool(item.get("eligible")) for item in validation.structured_provenance
            ),
            "disclosure": all(
                bool(item.get("allowed")) for item in validation.disclosure_checks
            ),
            "pdf_text": extracted_text_path.stat().st_size > 0,
            "pdf_text_quality": pdf_text_quality["status"],
            "preview": preview_path.is_file(),
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    _restrict_private_tree(target_dir)
    return BuildResult(
        target=target,
        output_dir=target_dir,
        pdf_path=pdf_path,
        preview_path=preview_path,
        evidence_report_path=evidence_report_path,
        audit_report_path=audit_report_path,
        manifest_path=manifest_path,
        extracted_text_path=extracted_text_path,
        page_count=page_count,
        validation=validation,
    )
