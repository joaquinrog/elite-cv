from __future__ import annotations

import json
from pathlib import Path

from experiments.renderer_decision.harness import (
    CommandAdapter,
    measure_run,
    redact_error,
    summarize_repeatability,
)


def test_redact_error_removes_absolute_paths_and_limits_output():
    message = "failed at /home/private/cv/build/file.tex\n" + ("x" * 5000)

    result = redact_error(message, Path("/tmp/work"))

    assert "/home/" not in result
    assert len(result) <= 1000


def test_measure_run_records_sizes_text_quality_and_target_role(tmp_path):
    pdf = tmp_path / "cv.pdf"
    preview = tmp_path / "preview.png"
    text = tmp_path / "cv.txt"
    pdf.write_bytes(b"synthetic pdf")
    preview.write_bytes(b"synthetic preview")
    text.write_text("Synthetic Candidate\nData Engineer\n", encoding="utf-8")

    result = measure_run(
        candidate="mock",
        fixture="short",
        output_dir=tmp_path,
        pdf_path=pdf,
        preview_path=preview,
        text_path=text,
        expected_text=["Synthetic Candidate", "Data Engineer"],
        target_role="Product Designer",
        page_count=1,
        elapsed_seconds=0.25,
        links=["https://example.invalid/portfolio"],
        annotation_urls=set(),
    )

    assert result["artifact_sizes_bytes"] == {"cv.pdf": 13, "preview.png": 17, "cv.txt": 34}
    assert result["text_quality"]["status"] == "pass"
    assert result["target_role_absent"] is True
    assert result["links"][0]["status"] == "missing"
    assert result["page_count"] == 1
    assert result["paths"] == {"pdf": "cv.pdf", "preview": "preview.png", "text": "cv.txt"}


def test_command_adapter_reports_missing_tool_without_running_build(monkeypatch, tmp_path):
    adapter = CommandAdapter("typst", ("typst", "compile"))
    monkeypatch.setattr("shutil.which", lambda _: None)

    availability = adapter.availability()

    assert availability == {"available": False, "version": None, "error": "missing_tool"}
    assert adapter.build(tmp_path, tmp_path / "out")["status"] == "blocked"


def test_repeatability_hashes_are_stable():
    first = {"pdf_sha256": "same", "preview_sha256": "same"}
    second = {"pdf_sha256": "same", "preview_sha256": "same"}

    assert summarize_repeatability(first, second) == {"comparable": True, "identical": True}
