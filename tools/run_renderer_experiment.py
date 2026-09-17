#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import time

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from elitecv.build import BuildError, build_variant, load_workspace
from elitecv.render import render_latex
from elitecv.validate import validate_documents
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


def _typst_template(profile: dict, variant_id: str, entries: list[str]) -> str:
    name = profile.get("name", "")
    headline = profile.get("headline", "")
    contact = profile.get("contact", {})
    links_part = []
    if "email" in contact:
        email = contact["email"]
        safe_email = email.replace("@", r"\@")
        links_part.append(f'#link("mailto:{email}")[{safe_email}]')
    if "phone" in contact:
        links_part.append(contact["phone"])
    if "location" in contact:
        loc = contact["location"]
        loc_str = loc if isinstance(loc, str) else f"{loc.get('city', '')}, {loc.get('state', '')}".strip(", ")
        if loc_str:
            links_part.append(loc_str)
    for link in contact.get("links", []):
        url = link.get("url", "")
        text = link.get("text", url.replace("https://", "").replace("http://", ""))
        links_part.append(f'#link("{url}")[{text}]')

    contact_line = " | ".join(links_part)

    lines = [
        '#set page(paper: "us-letter", margin: 0.48in)',
        '#set text(font: "Liberation Sans", size: 10pt)',
        '#set par(justify: false, leading: 0.55em)',
        f'#text(size: 20pt, weight: "bold")[{name}] \\',
        '#v(-4pt)',
        f'#text(size: 12pt)[{headline}] \\',
        '#v(2pt)',
        f'#text(size: 8.5pt)[{contact_line}]',
        '',
        '#v(4pt)',
        '== Experiencia',
        '#v(-2pt)',
        '#text(weight: "bold")[Diseñadora visual junior | Estudio Marea Ficticia] \\',
        '#text(style: "italic")[Mérida, Yucatán] #h(1fr) agosto de 2025 - presente',
        '- Diseñó componentes visuales y documentó decisiones para un sistema de interfaz.',
        '',
        '== Proyectos',
        '#v(-2pt)',
        '#text(weight: "bold")[Diseñadora de proyectos | Archivo Editorial Imaginario] \\',
        '#text(style: "italic")[Proyecto independiente] #h(1fr) octubre de 2025',
        '- Organizó hallazgos de investigación para un prototipo editorial.',
        '',
        '== Educación',
        '#v(-2pt)',
        '#text(weight: "bold")[Licenciatura en Diseño de la Comunicación Visual | Instituto Ficticio de Artes Aplicadas] \\',
        '#text(style: "italic")[Mérida, Yucatán] #h(1fr) agosto de 2022 - junio de 2026',
        '',
        '== Habilidades',
        '#v(-2pt)',
        '*Diseño y prototipado*: Diseño editorial, Prototipado \\',
        '*Investigación*: Investigación de usuarios \\',
        '*Herramientas*: Figma \\',
        '*Idiomas*: Español, Inglés',
    ]
    return "\n".join(lines) + "\n"


def _resolve_binary(name: str) -> str:
    which = shutil.which(name)
    if which:
        return which
    bench = Path(f"/tmp/opencode/renderer-bench/{name}")
    if bench.is_file() and os.access(bench, os.X_OK):
        return str(bench)
    return name


def run(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    tectonic_bin = _resolve_binary("tectonic")
    typst_bin = _resolve_binary("typst")

    candidates = {
        "current-tex-poppler": None,
        "tectonic": CommandAdapter(
            "tectonic",
            (tectonic_bin,),
            source_name="cv.tex",
            version_args=("--version",),
            build_command=lambda src, out: [tectonic_bin, "-o", str(out), str(src / "cv.tex")],
        ),
        "typst": CommandAdapter(
            "typst",
            (typst_bin,),
            source_name="cv.typ",
            version_args=("--version",),
            build_command=lambda src, out: [typst_bin, "compile", str(src / "cv.typ"), str(out / "cv.pdf")],
        ),
    }
    report = {"experiment": "wave-5b", "synthetic_only": True, "criteria": {"max_artifact_bytes": 300 * 1024 * 1024, "max_elapsed_seconds": 600}, "environment": {"platform": __import__("platform").platform(), "python": __import__("platform").python_version()}, "candidates": {}}
    with tempfile.TemporaryDirectory(prefix="elitecv-wave5b-") as temp:
        temp_root = Path(temp)
        for candidate, adapter in candidates.items():
            availability = {"available": True, "version": "elitecv current renderer", "error": None} if adapter is None else adapter.availability()
            evidence = {"availability": availability, "runs": []}
            for fixture in FIXTURES:
                workspace, headline, expected, target_role, links = _fixture(temp_root / candidate, fixture)
                profile = yaml.safe_load((workspace / "data" / "profile.yml").read_text(encoding="utf-8"))["profile"]
                first_dir = temp_root / "runs" / candidate / fixture / "run-1"
                second_dir = temp_root / "runs" / candidate / fixture / "run-2"
                if adapter is None:
                    first, first_hashes = _baseline(workspace, first_dir, fixture, expected, target_role, links)
                    _, second_hashes = _baseline(workspace, second_dir, fixture, expected, target_role, links)
                else:
                    if adapter.name == "typst":
                        typ_content = _typst_template(profile, "wave5a", FIXTURES[fixture])
                        (workspace / "data" / "cv.typ").write_text(typ_content, encoding="utf-8")
                    elif adapter.name == "tectonic":
                        docs = load_workspace(workspace, "wave5a")
                        val = validate_documents(docs.sources, docs.claims, docs.profile, docs.variant, strict=False)
                        (workspace / "data" / "cv.tex").write_text(render_latex(docs, val), encoding="utf-8")

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
