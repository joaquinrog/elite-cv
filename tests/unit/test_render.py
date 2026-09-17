from elitecv.render import latex_escape
from elitecv.locale import format_date_range, get_locale


def test_latex_escape_handles_reserved_characters():
    value = r"50% & C++_v2 #1 $ {safe} \\ ~ ^"

    escaped = latex_escape(value)

    assert r"50\%" in escaped
    assert r"\&" in escaped
    assert r"C++\_v2" in escaped
    assert r"\#1" in escaped
    assert r"\$" in escaped
    assert r"\{safe\}" in escaped
    assert r"\textbackslash{}" in escaped
    assert r"\textasciitilde{}" in escaped
    assert r"\textasciicircum{}" in escaped


def test_supported_locales_format_labels_and_month_ranges():
    assert get_locale("en-US").section("experience") == "Experience"
    assert get_locale("es-MX").section("experience") == "Experiencia"
    assert format_date_range("2025-10", "2025-10", "es-MX") == "octubre de 2025"
    assert format_date_range("2025-08", None, "es-MX") == "agosto de 2025 - presente"
    assert format_date_range("2024-04", "2025-01", "en-US") == "April 2024 - January 2025"
    assert format_date_range("2025-10-03", "2025-10-03", "es-MX") == "3 de octubre de 2025"
    assert format_date_range("2025-10-03", "2025-10-03", "en-US") == "October 3, 2025"


def test_unsupported_locale_fails_clearly():
    import pytest

    with pytest.raises(ValueError, match="Unsupported locale"):
        get_locale("fr-FR")


def test_project_entry_formatting_highlights_project_name():
    from elitecv.render import _render_entry

    project_entry = {
        "section": "projects",
        "organization": "OpenCode Multi-Agent",
        "role": "Personal Project",
        "location": "Multi-provider LLM systems",
        "start_date": "2026-01",
        "end_date": "2026-09",
        "bullets": [{"text": "Engineered agent orchestration system."}],
    }

    rendered = _render_entry(project_entry, "en-US")
    lines = rendered.splitlines()
    assert r"\textbf{OpenCode Multi-Agent} \hfill January 2026 - September 2026\\[-1pt]" == lines[0]
    assert r"\textit{Personal Project | Multi-provider LLM systems}" == lines[1]
