from __future__ import annotations

from dataclasses import dataclass
from datetime import date


MONTHS = {
    "en-US": (
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ),
    "es-MX": (
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
    ),
}


@dataclass(frozen=True)
class Locale:
    code: str
    present: str
    sections: dict[str, str]

    def section(self, key: str) -> str:
        return self.sections.get(key, key.replace("_", " ").title())

    def month(self, year: int, month: int) -> str:
        if self.code == "es-MX":
            return f"{MONTHS[self.code][month - 1]} de {year}"
        return f"{MONTHS[self.code][month - 1]} {year}"


def get_locale(code: str) -> Locale:
    if code not in MONTHS:
        raise ValueError(f"Unsupported locale: {code!r}; supported locales are en-US and es-MX")
    if code == "es-MX":
        return Locale(code, "presente", {"experience": "Experiencia", "projects": "Proyectos", "education": "Educación", "skills": "Habilidades"})
    return Locale(code, "Present", {"experience": "Experience", "projects": "Projects", "education": "Education", "skills": "Skills"})


def _format_date(value: str, locale: Locale) -> str:
    parts = value.split("-")
    if len(parts) == 1:
        return value
    parsed = date.fromisoformat(value + ("-01" if len(parts) == 2 else ""))
    if len(parts) == 2:
        return locale.month(parsed.year, parsed.month)
    if locale.code == "es-MX":
        return f"{parsed.day} de {MONTHS[locale.code][parsed.month - 1]} de {parsed.year}"
    return f"{MONTHS[locale.code][parsed.month - 1]} {parsed.day}, {parsed.year}"


def format_date_range(start: str | None, end: str | None, locale_code: str) -> str:
    locale = get_locale(locale_code)
    if not start:
        return locale.present if not end else _format_date(end, locale)
    start_text = _format_date(start, locale)
    if end is None:
        return f"{start_text} - {locale.present}"
    end_text = _format_date(end, locale)
    return start_text if start == end else f"{start_text} - {end_text}"
