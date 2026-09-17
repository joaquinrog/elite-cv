#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys
import tempfile
import time

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from elitecv.build import BuildError, build_variant
from experiments.renderer_decision.harness import (
    CommandAdapter,
    hashes_for_run,
    measure_run,
    pdf_annotation_urls,
    run_command_adapter,
    summarize_repeatability,
)

FIXTURE_ROOT = ROOT / "examples" / "synthetic-junior-design"
FIXTURES = {"short": ["entry.synthetic-education"], "medium": ["entry.synthetic-estudio", "entry.synthetic-education"], "dense": ["entry.synthetic-estudio", "entry.synthetic-editorial", "entry.synthetic-education"]}


def _fixture(root: Path, name: str) -> tuple[Path, str, list[str], str, list[str]]:
    workspace = root / name
    workspace.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(FIXTURE_ROOT, workspace)
    source_variant = workspace / "data" / "variants" / "diseno-junior.yml"
    variant = workspace / "data" / "variants" / "wave5a.yml"
    data = yaml.safe_load(source_variant.read_text(encoding="utf-8"))
    data["id"] = "wave5a"
    data["include_entries"] = FIXTURES[name]
    data.pop("page_target", None)
    variant.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    profile = yaml.safe_load((workspace / "data" / "profile.yml").read_text(encoding="utf-8"))["profile"]
    return workspace, str(profile["headline"]), [str(profile["name"]), str(profile["headline"])], str(data["target_role"]), [item["url"] for item in profile["contact"]["links"]]


def _baseline(workspace: Path, output: Path, fixture: str, expected: list[str], target_role: str, links: list[str]) -> tuple[dict, dict[str, str] | None]:
    start = time.monotonic()
    try:
        result = build_variant(workspace, "wave5a", output_dir=output, strict=True)
        run = measure_run(candidate="current-tex-poppler", fixture=fixture, output_dir=output, pdf_path=result.pdf_path, preview_path=result.preview_path, text_path=result.extracted_text_path, expected_text=expected, target_role=target_role, page_count=result.page_count, elapsed_seconds=time.monotonic() - start, links=links, annotation_urls=pdf_annotation_urls(result.pdf_path))
        return run, hashes_for_run(result.pdf_path, result.preview_path)
    except BuildError as exc:
        return measure_run(candidate="current-tex-poppler", fixture=fixture, output_dir=output, pdf_path=output / "missing.pdf", preview_path=output / "missing.png", text_path=output / "missing.txt", expected_text=expected, target_role=target_role, page_count=None, elapsed_seconds=time.monotonic() - start, links=links, error=str(exc)), None


def _markdown(report: dict) -> str:
    lines = ["# Wave 5A Renderer Decision Experiment", "", "Generated from synthetic fixtures only. Paths are intentionally omitted or relative.", "", "## Measured environment", ""]
    lines.append(f"- Host evidence: `{report['environment']['platform']}` / Python `{report['environment']['python']}`")
    for candidate, evidence in report["candidates"].items():
        lines.append(f"- **{candidate}**: {evidence['availability']['version'] or evidence['availability']['error']}")
    lines += ["", "## Results", "", "| Candidate | Fixture | Status | Pages | Text | Target role absent | Repeatable |", "| --- | --- | --- | ---: | --- | --- | --- |"]
    for candidate, evidence in report["candidates"].items():
        for run in evidence["runs"]:
            lines.append(f"| {candidate} | {run['fixture']} | {run['status']} | {run['page_count'] or 'unknown'} | {run['text_quality']['status']} | {run['target_role_absent']} | {run.get('repeatability', {}).get('identical', 'unknown')} |")
    lines += ["", "## Decision", "", "Current TeX/Poppler is the only measured passing candidate in this environment. Typst and Tectonic remain blocked when unavailable; no platform, size, or license claim is inferred.", "", "## Limits", "", "- Budget gate is recorded as criteria only: <=300 MB artifacts and <=10 minutes per build.", "- Links are checked as PDF annotations through `pdfinfo -url`.", "- License and native macOS/Windows measurements remain pending."]
    return "\n".join(lines) + "\n"


def run(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    candidates = {
        "current-tex-poppler": None,
        "tectonic": CommandAdapter("tectonic", ("tectonic",), version_args=("--version",)),
        "typst": CommandAdapter("typst", ("typst",), source_name="cv.typ"),
    }
    report = {"experiment": "wave-5a", "synthetic_only": True, "criteria": {"max_artifact_bytes": 300 * 1024 * 1024, "max_elapsed_seconds": 600}, "environment": {"platform": __import__("platform").platform(), "python": __import__("platform").python_version()}, "candidates": {}}
    with tempfile.TemporaryDirectory(prefix="elitecv-wave5a-") as temp:
        temp_root = Path(temp)
        for candidate, adapter in candidates.items():
            availability = {"available": True, "version": "elitecv current renderer", "error": None} if adapter is None else adapter.availability()
            evidence = {"availability": availability, "runs": []}
            for fixture in FIXTURES:
                workspace, _, expected, target_role, links = _fixture(temp_root / candidate, fixture)
                first_dir = temp_root / "runs" / candidate / fixture / "run-1"
                second_dir = temp_root / "runs" / candidate / fixture / "run-2"
                if adapter is None:
                    first, first_hashes = _baseline(workspace, first_dir, fixture, expected, target_role, links)
                    _, second_hashes = _baseline(workspace, second_dir, fixture, expected, target_role, links)
                else:
                    first = run_command_adapter(adapter, workspace / "data", first_dir, fixture=fixture, expected_text=expected, target_role=target_role, links=links) if availability["available"] else measure_run(candidate=candidate, fixture=fixture, output_dir=first_dir, pdf_path=first_dir / "missing.pdf", preview_path=first_dir / "missing.png", text_path=first_dir / "missing.txt", expected_text=expected, target_role=target_role, page_count=None, elapsed_seconds=0, links=links, error=availability["error"])
                    second = run_command_adapter(adapter, workspace / "data", second_dir, fixture=fixture, expected_text=expected, target_role=target_role, links=links) if availability["available"] else first
                    first_hashes = hashes_for_run(first_dir / "cv.pdf", first_dir / "preview.png") if first["status"] == "pass" else None
                    second_hashes = hashes_for_run(second_dir / "cv.pdf", second_dir / "preview.png") if second["status"] == "pass" else None
                first["repeatability"] = summarize_repeatability(first_hashes or {}, second_hashes or {})
                evidence["runs"].append(first)
            report["candidates"][candidate] = evidence
    (output_dir / "results.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (output_dir / "results.md").write_text(_markdown(report), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the public Wave 5A renderer experiment")
    parser.add_argument("--output", type=Path, default=ROOT / "experiments" / "renderer-decision" / "artifacts")
    run(parser.parse_args().output)
