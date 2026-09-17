import json
from pathlib import Path

from elitecv.models import load_workspace
from elitecv.report import render_audit_report, render_evidence_report
from elitecv.validate import validate_documents


ROOT = Path(__file__).parents[2]


def _documents_and_validation():
    documents = load_workspace(ROOT / "examples" / "synthetic-profile", "robotics-software")
    validation = validate_documents(
        documents.sources,
        documents.claims,
        documents.profile,
        documents.variant,
        strict=True,
    )
    return documents, validation


def test_reports_expose_three_independent_audit_categories_without_source_excerpts():
    documents, validation = _documents_and_validation()

    evidence = render_evidence_report(documents, validation, page_count=1, tool_version="test")
    audit = render_audit_report(documents, validation, page_count=1, extracted_text_path="private/cv.txt")

    for text in (evidence, audit):
        assert "Bullet traceability" in text
        assert "Structured-field provenance" in text
        assert "Disclosure checks" in text
        assert "excerpt:" not in text.lower()
    assert "aggregate" not in audit.lower()


def test_manifest_contract_names_categories_separately(tmp_path):
    from elitecv.build import build_variant

    result = build_variant(ROOT / "examples" / "synthetic-profile", "robotics-software", output_dir=tmp_path)
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

    assert set(manifest) >= {"bullet_traceability", "structured_field_provenance", "disclosure_checks"}
    assert manifest["traceability_coverage"] == 1.0
    assert manifest["traceability_scope"] == "selected_bullets"
    assert manifest["bullet_traceability"]["scope"] == "selected_bullets"
    assert manifest["structured_field_provenance"]
    assert manifest["disclosure_checks"]
