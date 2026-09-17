from __future__ import annotations

from pathlib import Path
from typing import Any

from .models import WorkspaceDocuments
from .locale import format_date_range, get_locale
from .validate import ValidationResult


DENSITY_TEX = {
    "short": "\n".join((r"\newcommand{\CVMargin}{0.62in}", r"\newcommand{\CVLeading}{1.04}", r"\newcommand{\CVSectionBefore}{8pt}", r"\newcommand{\CVSectionAfter}{3pt}", r"\newcommand{\CVItemSep}{2pt}")),
    "medium": "\n".join((r"\newcommand{\CVMargin}{0.55in}", r"\newcommand{\CVLeading}{1.00}", r"\newcommand{\CVSectionBefore}{6pt}", r"\newcommand{\CVSectionAfter}{2pt}", r"\newcommand{\CVItemSep}{1pt}")),
    "dense": "\n".join((r"\newcommand{\CVMargin}{0.48in}", r"\newcommand{\CVLeading}{0.96}", r"\newcommand{\CVSectionBefore}{4pt}", r"\newcommand{\CVSectionAfter}{1pt}", r"\newcommand{\CVItemSep}{0pt}")),
}


def latex_escape(value: str) -> str:
    """Escape user-controlled text before it enters a LaTeX document."""

    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(character, character) for character in str(value))


def _url_escape(value: str) -> str:
    return latex_escape(value).replace(r"\textbackslash{}", "")


def _date_range(entry: dict[str, Any], locale_code: str) -> str:
    start = entry.get("start_date") or ""
    return format_date_range(start, entry.get("end_date"), locale_code)


def _entry_title(entry: dict[str, Any]) -> str:
    role = entry.get("role") or entry.get("title") or ""
    organization = entry.get("organization") or ""
    return f"{role} | {organization}" if role and organization else str(role or organization)


def _render_contact(profile: dict[str, Any], variant: dict[str, Any]) -> str:
    contact = profile.get("contact", {}) or {}
    parts: list[str] = []
    for field_name in variant.get("contact_fields", []) or []:
        if field_name == "email" and contact.get("email"):
            email = str(contact["email"])
            parts.append(f"\\href{{mailto:{_url_escape(email)}}}{{{latex_escape(email)}}}")
        elif field_name in {"phone", "location"} and contact.get(field_name):
            parts.append(latex_escape(str(contact[field_name])))
        elif field_name == "links":
            for link in contact.get("links", []) or []:
                if not isinstance(link, dict):
                    continue
                url = str(link.get("url", ""))
                label = str(link.get("label") or url)
                if url:
                    parts.append(f"\\href{{{_url_escape(url)}}}{{{latex_escape(label)}}}")
    return r" \textbar{} ".join(parts)


def _render_skill_groups(profile: dict[str, Any], variant: dict[str, Any]) -> str:
    groups = {
        str(group.get("id")): group
        for group in profile.get("skill_groups", []) or []
        if isinstance(group, dict)
    }
    rows: list[str] = []
    for group_id in variant.get("include_skill_groups", []) or []:
        group = groups.get(str(group_id))
        if not group:
            continue
        items = [
            str(item.get("name", ""))
            for item in group.get("items", []) or []
            if isinstance(item, dict) and item.get("name")
        ]
        if items:
            rows.append(f"\\textbf{{{latex_escape(str(group.get('label', '')))}}}: "
                        f"{', '.join(latex_escape(item) for item in items)}\\\\")
    return "\n".join(rows)


def _render_entry(entry: dict[str, Any], locale_code: str) -> str:
    lines = [f"\\textbf{{{latex_escape(_entry_title(entry))}}}\\\\[-1pt]"]
    location = entry.get("location")
    metadata = f"\\textit{{{latex_escape(str(location))}}}" if location else ""
    lines.append(f"{metadata} \\hfill {latex_escape(_date_range(entry, locale_code))}")
    bullets = entry.get("bullets", []) or []
    if bullets:
        lines.append(r"\begin{itemize}")
        for bullet in bullets:
            lines.append(f"  \\item {latex_escape(str(bullet.get('text', '')))}")
        lines.append(r"\end{itemize}")
    return "\n".join(lines)


def render_latex(documents: WorkspaceDocuments, validation: ValidationResult) -> str:
    profile = documents.profile["profile"]
    variant = documents.variant
    locale = get_locale(str(variant.get("locale", "en-US")))
    sections: list[str] = []
    entries_by_section: dict[str, list[dict[str, Any]]] = {}
    for entry in validation.selected_entries:
        entries_by_section.setdefault(str(entry.get("section", "experience")), []).append(entry)

    for section in variant.get("sections", []):
        if section == "skills":
            skill_text = _render_skill_groups(profile, variant)
            if skill_text:
                sections.append(f"\\cvsection{{{locale.section('skills')}}}\n{skill_text}")
            continue
        entries = entries_by_section.get(section, [])
        if not entries:
            continue
        body = "\n\n".join(_render_entry(entry, locale.code) for entry in entries)
        sections.append(f"\\cvsection{{{locale.section(section)}}}\n{body}")

    template_path = Path(__file__).resolve().parents[1] / "templates" / "default" / "resume.tex"
    if not template_path.is_file():
        template_path = Path(__file__).with_name("template.tex")
    template = template_path.read_text(encoding="utf-8")
    page_size = str(variant.get("page_size", "letter"))
    if page_size not in {"letter", "a4"}:
        page_size = "letter"
    density = str(variant.get("density", "medium"))
    density_tex = DENSITY_TEX.get(density, DENSITY_TEX["medium"])
    values = {
        "{{PAGE_SIZE}}": page_size,
        "{{DENSITY}}": density_tex,
        "{{NAME}}": latex_escape(str(profile.get("name", ""))),
        "{{HEADLINE}}": latex_escape(str(profile.get("headline", ""))),
        "{{CONTACT}}": _render_contact(profile, variant),
        "{{SECTIONS}}": "\n\n".join(sections),
    }
    for placeholder, value in values.items():
        template = template.replace(placeholder, value)
    return template
