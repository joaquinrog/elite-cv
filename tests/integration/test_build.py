from pathlib import Path
import shutil
import subprocess

import pytest
import yaml

from elitecv.build import BuildError, _run, build_variant


SAMPLE_ROOT = Path(__file__).parents[2] / "examples" / "synthetic-profile"
REQUIRED_TOOLS = ("latexmk", "pdflatex", "pdftotext", "pdftoppm", "pdfinfo")


@pytest.mark.skipif(
    any(shutil.which(tool) is None for tool in REQUIRED_TOOLS),
    reason="local PDF toolchain is not installed",
)
def test_synthetic_variant_build_produces_share_and_private_outputs(tmp_path):
    result = build_variant(SAMPLE_ROOT, "robotics-software", output_dir=tmp_path)

    assert result.page_count == 1
    assert result.validation.traceability_coverage == 1.0
    assert result.pdf_path.is_file()
    assert result.preview_path.is_file()
    assert result.evidence_report_path.is_file()
    assert result.audit_report_path.is_file()
    assert result.manifest_path.is_file()
    extracted_text = result.extracted_text_path.read_text(encoding="utf-8")
    assert "Robotics Software Intern" in extracted_text
    assert "2024-04 - 2025-01" in extracted_text
    report = result.evidence_report_path.read_text(encoding="utf-8")
    assert "35 percent faster" not in report
    assert "raw source excerpts" in report


def test_strict_build_rejects_a_bullet_with_a_missing_claim(tmp_path):
    workspace = tmp_path / "workspace"
    shutil.copytree(SAMPLE_ROOT, workspace)
    profile_path = workspace / "data" / "profile.yml"
    profile = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
    profile["profile"]["entries"][0]["bullets"][0]["claim_ids"] = ["claim.missing"]
    profile_path.write_text(yaml.safe_dump(profile, sort_keys=False), encoding="utf-8")

    with pytest.raises(BuildError, match=r"bullet `bullet\.synthetic-control`.*claim\.missing"):
        build_variant(workspace, "robotics-software", output_dir=tmp_path / "dist")


def test_tool_timeout_is_reported_as_a_build_error(monkeypatch, tmp_path):
    def timeout(*_args, **_kwargs):
        raise subprocess.TimeoutExpired("pdflatex", 60)

    monkeypatch.setattr("elitecv.build.subprocess.run", timeout)

    with pytest.raises(BuildError, match="timed out"):
        _run(["pdflatex"], cwd=tmp_path)
