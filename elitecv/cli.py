from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Sequence

from . import __version__
from .build import BuildError, build_variant
from .diagnostics import check_dependencies, dependency_check_json, required_dependency_failures
from .approval import ApprovalError, approve_claims
from .intake import IntakeError, apply_intake_proposal, intake_source
from .models import (
    WorkspaceError,
    data_directory,
    load_workspace,
    load_yaml,
    validate_variant_id,
)
from .safety import scan_public_tree
from .validate import format_issues, validate_documents


def _root(value: str) -> Path:
    return Path(value).expanduser().resolve()


def _restrict_private_path(path: Path, mode: int) -> None:
    if os.name == "posix":
        path.chmod(mode)


def _private_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    _restrict_private_path(path, 0o700)


def _write_private_file(path: Path, contents: str) -> None:
    path.write_text(contents, encoding="utf-8")
    _restrict_private_path(path, 0o600)


def _doctor(root: Path, *, json_output: bool = False) -> int:
    checks = check_dependencies()
    if json_output:
        import json

        print(json.dumps({"checks": [dependency_check_json(check) for check in checks]}, sort_keys=True))
        return 1 if required_dependency_failures(checks) else 0

    print(f"Elite CV Builder by joaq {__version__} doctor: {root}")
    for check in checks:
        if check.status == "pass":
            print(f"  OK   {check.check_id}")
        elif not check.required:
            print(f"  INFO {check.remediation}")
        else:
            print(f"  MISS {check.check_id}: {check.remediation}")
    if required_dependency_failures(checks):
        print("Doctor found missing dependencies; no build will silently skip them.")
        return 1
    print("Doctor passed.")
    return 0


def _validate(root: Path, target: str) -> int:
    try:
        documents = load_workspace(root, target)
    except WorkspaceError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1
    result = validate_documents(
        documents.sources,
        documents.claims,
        documents.profile,
        documents.variant,
        strict=False,
    )
    for issue in result.warnings:
        print(f"WARNING {issue}")
    if result.errors:
        print(format_issues(result.errors), file=sys.stderr)
        return 1
    coverage = (
        "not applicable"
        if result.selected_bullet_count == 0
        else f"{result.traceability_coverage:.0%}"
    )
    print(f"Valid draft: {target}; bullet traceability coverage {coverage}.")
    return 0


def _ensure_local_ignores(root: Path, *, track_structured_profile: bool) -> Path:
    entries = [
        "sources/private/**",
        "workspace/**",
        "dist/**",
    ]
    if not track_structured_profile:
        entries.extend(["data/*.yml", "data/variants/*.yml"])
    git_exclude = root / ".git" / "info" / "exclude"
    ignore_path = git_exclude if git_exclude.is_file() else root / ".gitignore"
    ignore_path.parent.mkdir(parents=True, exist_ok=True)
    existing = ignore_path.read_text(encoding="utf-8") if ignore_path.exists() else ""
    marker = "# Elite CV local defaults"
    end_marker = "# End Elite CV local defaults"
    block = marker + "\n" + "\n".join(entries) + "\n" + end_marker + "\n"
    if marker in existing:
        before = existing.split(marker, 1)[0]
        if end_marker in existing:
            after = existing.split(end_marker, 1)[1]
        else:
            after = ""
        ignore_path.write_text(before + block + after.lstrip("\n"), encoding="utf-8")
    else:
        separator = "\n" if existing and not existing.endswith("\n") else ""
        ignore_path.write_text(existing + separator + block, encoding="utf-8")
    return ignore_path


def _init(
    root: Path,
    target_role: str,
    page_size: str,
    *,
    track_structured_profile: bool = False,
    allow_remote_artifacts: bool = False,
) -> int:
    data_dir = root / "data"
    variants_dir = data_dir / "variants"
    _private_directory(data_dir)
    _private_directory(variants_dir)
    _private_directory(root / "sources" / "private")
    _private_directory(root / "workspace")
    _private_directory(root / "workspace" / "review")
    _private_directory(root / "dist")
    skeletons = {
        "sources.yml": "schema_version: 2\nsources: []\n",
        "claims.yml": "schema_version: 2\nclaims: []\n",
        "profile.yml": "schema_version: 2\nprofile:\n  id: profile.local\n  name: \"Your Name\"\n  headline: \"Technical role\"\n  headline_claim_ids: []\n  contact:\n    email: \"you@example.com\"\n    phone: null\n    location: null\n    links: []\n  entries: []\n  skill_groups: []\n",
    }
    for name, contents in skeletons.items():
        path = data_dir / name
        if not path.exists():
            _write_private_file(path, contents)
        else:
            _restrict_private_path(path, 0o600)
    variant_path = variants_dir / "general.yml"
    if not variant_path.exists():
        _write_private_file(
            variant_path,
            f"schema_version: 2\nid: general\ntarget_role: {target_role!r}\nlocale: en-US\npage_size: {page_size}\npage_target: 1\nsections: [experience, projects, education, skills]\ninclude_entries: []\nexclude_entries: []\nrequired_claim_ids: []\nallowed_disclosures: [shareable]\ninclude_skill_groups: []\ncontact_fields: []\n",
        )
    else:
        _restrict_private_path(variant_path, 0o600)
    questions = root / "workspace" / "review" / "open-questions.md"
    if not questions.exists():
        _write_private_file(
            questions,
            "# Open questions\n\n- [ ] Add and review source records before building a personal CV.\n",
        )
    else:
        _restrict_private_path(questions, 0o600)
    _ensure_local_ignores(root, track_structured_profile=track_structured_profile)
    _write_private_file(
        root / "workspace" / "policy.yml",
        "schema_version: 1\n"
        "privacy:\n"
        f"  track_structured_profile: {'true' if track_structured_profile else 'false'}\n"
        f"  remote_artifacts: {'true' if allow_remote_artifacts else 'false'}\n"
        "  hosted_agent_sources: prompt\n",
    )
    print(f"Initialized local workspace at {root}")
    print(
        "Structured profile tracking: "
        + ("enabled by explicit opt-in." if track_structured_profile else "disabled by default.")
    )
    print(
        "Remote artifacts: "
        + ("enabled by explicit opt-in." if allow_remote_artifacts else "disabled by default.")
    )
    print("Raw sources, workspace notes, and generated dist/ artifacts are local-only by default.")
    print("Hosted agents may transmit source material to their provider; review that policy before use.")
    return 0


def _review(root: Path) -> int:
    try:
        data_dir = data_directory(root)
        claims = load_yaml(data_dir / "claims.yml").get("claims", [])
    except WorkspaceError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1
    questions: list[str] = ["# Open questions", ""]
    for claim in claims:
        if claim.get("evidence_status") in {"unsupported", "conflicted"} or claim.get("review_status") != "approved":
            questions.append(
                f"- [ ] Review `{claim.get('id', 'unknown')}`: {claim.get('evidence_status', 'unknown')} / {claim.get('review_status', 'unknown')} / {claim.get('disclosure', 'unknown')}"
            )
    if len(questions) == 2:
        questions.append("- [x] No unresolved claim states found.")
    path = root / "workspace" / "review" / "open-questions.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(questions) + "\n", encoding="utf-8")
    print(path)
    return 0


def _status(root: Path) -> int:
    try:
        data_dir = data_directory(root)
        claims = load_yaml(data_dir / "claims.yml").get("claims", [])
        profile = load_yaml(data_dir / "profile.yml").get("profile", {})
        variants = sorted((data_dir / "variants").glob("*.yml"))
    except WorkspaceError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1
    states: dict[str, int] = {}
    for claim in claims:
        key = f"{claim.get('evidence_status', 'unknown')}/{claim.get('review_status', 'unknown')}/{claim.get('disclosure', 'unknown')}"
        states[key] = states.get(key, 0) + 1
    print(f"Workspace: {root}")
    print(f"Profile: {profile.get('id', 'missing')}")
    print(f"Claims: {len(claims)}")
    for state, count in sorted(states.items()):
        print(f"  {state}: {count}")
    print(f"Variants: {', '.join(path.stem for path in variants) or 'none'}")
    print(f"Private sources path: {root / 'sources' / 'private'}")
    print(f"Generated output path: {root / 'dist'}")
    return 0


def _release(root: Path, target: str, acknowledge: bool) -> int:
    if not acknowledge:
        print(
            "ERROR release requires human review acknowledgment. Re-run with --acknowledge-visual-review after inspecting the PDF and evidence report.",
            file=sys.stderr,
        )
        return 1
    try:
        result = build_variant(root, target, strict=True)
    except BuildError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1
    release_dir = result.output_dir / "release"
    if release_dir.exists():
        shutil.rmtree(release_dir)
    _private_directory(release_dir)
    for path in (result.pdf_path, result.preview_path):
        destination = release_dir / path.name
        shutil.copy2(path, destination)
        _restrict_private_path(destination, 0o600)
    print(f"Released local share bundle: {release_dir}")
    print("Nothing was uploaded or published.")
    return 0


def _check_public(root: Path) -> int:
    findings = scan_public_tree(root)
    if findings:
        for finding in findings:
            print(f"ERROR {finding.code}: {finding.path}: {finding.message}")
        print("Public safety checks are guardrails, not a privacy guarantee.", file=sys.stderr)
        return 1
    print("Public safety scan passed. This is a guardrail, not a privacy guarantee.")
    return 0


def _intake(root: Path, source: Path, target_role: str, locale: str, hosted_processing: str) -> int:
    try:
        result = intake_source(root, source, target_role, locale, hosted_processing)
    except IntakeError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1
    print(f"Registered source {result.source_id}")
    print(f"Variant: {result.variant_id}")
    print("Structured mapping: pending")
    print(f"Hosted processing: {hosted_processing}")
    return 0


def _intake_apply(root: Path, source_id: str, proposal: Path) -> int:
    try:
        result = apply_intake_proposal(root, source_id, proposal)
    except IntakeError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1
    print(f"Applied proposal for {result.source_id}; {result.question_count} questions queued.")
    return 0


def _approve(root: Path, source_id: str, reviewer: str, claim_ids: list[str], disclosure: str, contact_fields: list[str]) -> int:
    try:
        result = approve_claims(root, source_id, reviewer, claim_ids, disclosure, contact_fields)
    except ApprovalError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1
    print(f"Approved {len(result.approved_claim_ids)} claims for {result.source_id}.")
    return 0


def _variant_create(root: Path, variant_id: str) -> int:
    try:
        data_dir = data_directory(root)
        variant_id = validate_variant_id(variant_id)
    except WorkspaceError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1
    template_path = data_dir / "variants" / "general.yml"
    variants_dir = (data_dir / "variants").resolve()
    destination = (variants_dir / f"{variant_id}.yml").resolve()
    try:
        destination.relative_to(variants_dir)
    except ValueError:
        print("ERROR variant id resolves outside the variants directory", file=sys.stderr)
        return 1
    if destination.exists():
        print(f"ERROR variant already exists: {destination}", file=sys.stderr)
        return 1
    if not template_path.exists():
        print("ERROR no variant template available", file=sys.stderr)
        return 1
    text = template_path.read_text(encoding="utf-8").replace("id: general", f"id: {variant_id}", 1)
    _write_private_file(destination, text)
    print(destination)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="elitecv",
        description="Local-first, evidence-backed CVs with inspectable claim provenance.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="check local build dependencies")
    doctor.add_argument("--root", default=".", type=_root)
    doctor.add_argument("--json", action="store_true", dest="json_output")

    init = subparsers.add_parser("init", help="create a local private workspace")
    init.add_argument("--root", default=".", type=_root)
    init.add_argument("--target", default="General Technical Role")
    init.add_argument("--page-size", choices=("letter", "a4"), default="letter")
    init.add_argument("--track-structured-profile", action="store_true")
    init.add_argument("--allow-remote-artifacts", action="store_true")

    review = subparsers.add_parser("review", help="synchronize the local open-question checklist")
    review.add_argument("--root", default=".", type=_root)

    status = subparsers.add_parser("status", help="show profile and claim state counts")
    status.add_argument("--root", default=".", type=_root)

    validate = subparsers.add_parser("validate", help="validate structured data in draft mode")
    validate.add_argument("--root", default=".", type=_root)
    validate.add_argument("--target", required=True)

    build = subparsers.add_parser("build", help="validate and build a target PDF")
    build.add_argument("--root", default=".", type=_root)
    build.add_argument("--target", required=True)
    build.add_argument("--output-dir", type=_root)

    release = subparsers.add_parser("release", help="create a local share bundle after human review")
    release.add_argument("variant")
    release.add_argument("--root", default=".", type=_root)
    release.add_argument("--acknowledge-visual-review", action="store_true")

    public = subparsers.add_parser("check-public", help="scan the public extraction for obvious leaks")
    public.add_argument("--root", default=".", type=_root)

    intake = subparsers.add_parser("intake", help="register and extract one private source")
    intake.add_argument("--root", required=True, type=_root)
    intake.add_argument("--source", required=True, type=Path)
    intake.add_argument("--target-role", required=True)
    intake.add_argument("--locale", required=True, choices=("en-US", "es-MX"))
    intake.add_argument("--hosted-processing", required=True, choices=("approved", "denied"))

    intake_apply = subparsers.add_parser("intake-apply", help="apply a private agent proposal")
    intake_apply.add_argument("--root", required=True, type=_root)
    intake_apply.add_argument("--source-id", required=True)
    intake_apply.add_argument("--proposal", required=True, type=Path)

    approve = subparsers.add_parser("approve", help="approve selected claims from one source")
    approve.add_argument("--root", required=True, type=_root)
    approve.add_argument("--source-id", required=True)
    approve.add_argument("--reviewer", required=True)
    approve.add_argument("--claim-id", dest="claim_ids", action="append", required=True)
    approve.add_argument("--disclosure", required=True, choices=("private", "restricted", "shareable"))
    approve.add_argument("--contact-field", dest="contact_fields", action="append", default=[])

    variant = subparsers.add_parser("variant", help="manage target variants")
    variant_subparsers = variant.add_subparsers(dest="variant_command", required=True)
    create = variant_subparsers.add_parser("create", help="copy the default variant as a starting point")
    create.add_argument("variant_id")
    create.add_argument("--root", default=".", type=_root)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "doctor":
        return _doctor(args.root, json_output=args.json_output)
    if args.command == "init":
        return _init(
            args.root,
            args.target,
            args.page_size,
            track_structured_profile=args.track_structured_profile,
            allow_remote_artifacts=args.allow_remote_artifacts,
        )
    if args.command == "review":
        return _review(args.root)
    if args.command == "status":
        return _status(args.root)
    if args.command == "validate":
        return _validate(args.root, args.target)
    if args.command == "build":
        try:
            result = build_variant(args.root, args.target, output_dir=args.output_dir, strict=True)
        except BuildError as exc:
            print(f"ERROR {exc}", file=sys.stderr)
            return 1
        print(f"Built {result.pdf_path}")
        print(f"Evidence report: {result.evidence_report_path}")
        print(f"Audit report: {result.audit_report_path}")
        print(f"Manifest: {result.manifest_path}")
        return 0
    if args.command == "release":
        return _release(args.root, args.variant, args.acknowledge_visual_review)
    if args.command == "check-public":
        return _check_public(args.root)
    if args.command == "intake":
        return _intake(args.root, args.source, args.target_role, args.locale, args.hosted_processing)
    if args.command == "intake-apply":
        return _intake_apply(args.root, args.source_id, args.proposal)
    if args.command == "approve":
        return _approve(args.root, args.source_id, args.reviewer, args.claim_ids, args.disclosure, args.contact_fields)
    if args.command == "variant" and args.variant_command == "create":
        return _variant_create(args.root, args.variant_id)
    return 2
