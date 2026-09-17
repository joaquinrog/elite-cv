from pathlib import Path
import json
import shutil

import pytest

from elitecv.build import build_variant
from elitecv.cli import _doctor
from elitecv.models import load_workspace
from elitecv.render import render_latex
from elitecv.validate import validate_documents


FIXTURE_ROOT = Path(__file__).parents[2] / "examples" / "synthetic-junior-design"
TARGET = "diseno-junior"


def _documents():
    documents = load_workspace(FIXTURE_ROOT, TARGET)
    validation = validate_documents(
        documents.sources,
        documents.claims,
        documents.profile,
        documents.variant,
        strict=True,
    )
    return documents, validation


def test_wave0_fixture_is_public_and_fictional():
    assert FIXTURE_ROOT != Path(__file__).parents[2] / "examples" / "synthetic-profile"
    assert not any(part in {"private", "workspace", "dist"} for part in FIXTURE_ROOT.parts)
    documents, validation = _documents()

    assert validation.is_valid
    assert documents.variant["locale"] == "es-MX"
    assert documents.profile["profile"]["headline"] != documents.variant["target_role"]
    assert validation.traceability_coverage == 1.0


def test_wave0_fixture_keeps_iso_single_month_and_open_dates():
    documents, _ = _documents()
    entries = documents.profile["profile"]["entries"]
    single_month = next(entry for entry in entries if entry["id"] == "entry.synthetic-editorial")
    current = next(entry for entry in entries if entry["id"] == "entry.synthetic-estudio")

    assert (single_month["start_date"], single_month["end_date"]) == ("2025-10", "2025-10")
    assert current["start_date"] == "2025-08"
    assert current["end_date"] is None


def test_wave0_headline_isolated_from_targeting_metadata():
    documents, validation = _documents()
    latex = render_latex(documents, validation)

    assert "Diseñadora visual junior" in latex
    assert "Diseñadora de producto junior" not in latex


def test_wave0_es_mx_labels_and_dates_are_localized():
    documents, validation = _documents()
    latex = render_latex(documents, validation)

    assert "Experiencia" in latex
    assert "Proyectos" in latex
    assert "octubre de 2025" in latex
    assert "presente" in latex
    assert "Experience" not in latex
    assert "Present" not in latex


def test_wave0_contact_contract_renders_email_phone_location_and_two_links():
    documents, validation = _documents()
    latex = render_latex(documents, validation)

    for value in (
        "lucia.nava@example.com",
        "+52 55 0101 0101",
        "Mérida, Yucatán",
        "behance.net/lucia-nava",
        "lucianava.example.com",
    ):
        assert value in latex


def test_wave0_contact_rendering_uses_only_variant_allowlist_without_empty_separators():
    documents, validation = _documents()
    documents.variant["contact_fields"] = ["phone", "location"]

    latex = render_latex(documents, validation)

    assert "+52 55 0101 0101" in latex
    assert "Mérida, Yucatán" in latex
    assert "lucia.nava@example.com" not in latex
    assert "behance.net/lucia-nava" not in latex
    contact_line = next(line for line in latex.splitlines() if "+52 55 0101 0101" in line)
    assert contact_line.count(r"\textbar{}") == 1


def test_wave0_renderer_uses_only_selected_skill_groups_as_compact_rows():
    documents, validation = _documents()
    documents.variant["include_skill_groups"] = ["skills.tools"]

    latex = render_latex(documents, validation)

    assert "Herramientas" in latex
    assert "Figma" in latex
    assert "Diseño y prototipado" not in latex
    assert "Investigación" not in latex
    assert "Idiomas" not in latex


def test_wave0_documents_future_skill_groups_shape():
    documents, _ = _documents()
    groups = documents.profile["profile"]["skill_groups"]

    assert [group["id"] for group in groups] == [
        "skills.design",
        "skills.research",
        "skills.tools",
        "skills.languages",
    ]
    assert all(group["label"] and group["items"] for group in groups)


def test_wave0_doctor_checks_enumitem_dependency(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr("elitecv.cli.shutil.which", lambda _tool: "/usr/bin/tool")
    monkeypatch.setattr(
        "elitecv.cli.subprocess.run",
        lambda *_args, **_kwargs: type("Result", (), {"returncode": 0})(),
    )

    assert _doctor(tmp_path) == 0
    assert "enumitem" in capsys.readouterr().out


@pytest.mark.skipif(
    any(shutil.which(tool) is None for tool in ("latexmk", "pdflatex", "pdftotext", "pdftoppm", "pdfinfo")),
    reason="local PDF toolchain is not installed",
)
def test_wave0_extracted_text_has_a_privacy_safe_quality_classification(tmp_path):
    result = build_variant(FIXTURE_ROOT, TARGET, output_dir=tmp_path)
    text = result.extracted_text_path.read_text(encoding="utf-8")
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

    assert text.strip()
    assert "�" not in text
    assert manifest["checks"]["pdf_text_quality"] == "pass"
