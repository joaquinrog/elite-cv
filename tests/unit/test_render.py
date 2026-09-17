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
