from __future__ import annotations

from pathlib import Path
import re
import shutil

import pytest

from elitecv.build import build_variant
from elitecv.models import load_workspace
from elitecv.render import render_latex
from elitecv.validate import validate_documents


ROOT = Path(__file__).parents[2]
FIXTURE = ROOT / "examples" / "synthetic-junior-design"
VARIANTS = [f"{density}-{locale}-{paper}" for density in ("short", "medium", "dense") for locale in ("en-us", "es-mx") for paper in ("letter", "a4")]


def test_wave6a_density_contract_and_shared_editorial_template():
    default = (ROOT / "templates" / "default" / "resume.tex").read_text(encoding="utf-8")
    fallback = (ROOT / "elitecv" / "template.tex").read_text(encoding="utf-8")
    assert default == fallback
    assert "multicol" not in default
    assert "tikz" not in default
    assert "fontawesome" not in default
    assert "{{DENSITY}}" in default

    for target in VARIANTS:
        documents = load_workspace(FIXTURE, target)
        validation = validate_documents(documents.sources, documents.claims, documents.profile, documents.variant, strict=True)
        assert validation.is_valid, target
        assert documents.variant["density"] in {"short", "medium", "dense"}


def test_wave6a_render_is_linear_localized_and_has_clear_skills():
    for target in VARIANTS:
        documents = load_workspace(FIXTURE, target)
        validation = validate_documents(documents.sources, documents.claims, documents.profile, documents.variant, strict=True)
        latex = render_latex(documents, validation)
        section_labels = ("Experiencia", "Habilidades") if "es-mx" in target else ("Experience", "Skills")
        headings = [label for label in section_labels if label in latex]
        assert headings == [section_labels[1]] if target.startswith("short-") else headings == list(section_labels)
        assert "Technical skills" not in latex
        assert "\u2022" not in latex
        assert "\\href{" in latex


@pytest.mark.skipif(any(shutil.which(tool) is None for tool in ("latexmk", "pdflatex", "pdftotext", "pdftoppm", "pdfinfo")), reason="local PDF toolchain is not installed")
@pytest.mark.parametrize("target", VARIANTS)
def test_wave6a_build_matrix_is_one_page_extracted_and_linked(tmp_path, target):
    result = build_variant(FIXTURE, target, output_dir=tmp_path)
    assert result.page_count == 1
    text = result.extracted_text_path.read_text(encoding="utf-8")
    assert "Lucía Nava" in " ".join(text.split())
    if target.startswith("short-"):
        expected_section = "Educación" if "es-mx" in target else "Education"
    else:
        expected_section = "Experiencia" if "es-mx" in target else "Experience"
    assert expected_section in text
    assert "Diseño y prototipado" in text
    assert "Mérida, Yucatán" in text
    assert re.search(r"behance\.net/lucia-nava", text)
    assert "overfull" not in (result.output_dir / "private" / "build" / "cv.log").read_text(encoding="utf-8", errors="ignore") if (result.output_dir / "private" / "build" / "cv.log").exists() else True
