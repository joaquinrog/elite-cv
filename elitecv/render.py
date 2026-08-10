from __future__ import annotations

from pathlib import Path
from typing import Any

from .models import WorkspaceDocuments
from .validate import ValidationResult


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


def _date_range(entry: dict[str, Any]) -> str:
    start = entry.get("start_date") or ""
    end = entry.get("end_date") or "Present"
    return f"{start} - {end}" if start else str(end)


def _entry_title(entry: dict[str, Any]) -> str:
    role = entry.get("role") or entry.get("title") or ""
    organization = entry.get("organization") or ""
    return f"{role} | {organization}" if role and organization else str(role or organization)


def _render_contact(profile: dict[str, Any]) -> str:
    contact = profile.get("contact", {}) or {}
    parts: list[str] = []
    email = contact.get("email")
    if email:
        safe_email = latex_escape(email)
        parts.append(f"\\href{{mailto:{_url_escape(email)}}}{{{safe_email}}}")
    for link in contact.get("links", []) or []:
        if not isinstance(link, dict):
            continue
        url = str(link.get("url", ""))
        label = str(link.get("label") or url)
        if url:
            parts.append(f"\\href{{{_url_escape(url)}}}{{{latex_escape(label)}}}")
    return r" \textbar{} ".join(parts)


def _render_entry(entry: dict[str, Any]) -> str:
    lines = [
        f"\\textbf{{{latex_escape(_entry_title(entry))}}} \\hfill {latex_escape(_date_range(entry))}\\\\[-1pt]",
    ]
    location = entry.get("location")
    if location:
        lines.append(f"\\textit{{{latex_escape(str(location))}}}")
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
    sections: list[str] = []
    entries_by_section: dict[str, list[dict[str, Any]]] = {}
    for entry in validation.selected_entries:
        entries_by_section.setdefault(str(entry.get("section", "experience")), []).append(entry)

    section_labels = {
        "experience": "Experience",
        "projects": "Projects",
        "education": "Education",
    }
    for section in variant.get("sections", []):
        if section == "skills":
            skills = profile.get("skills", []) or []
            if skills:
                skill_text = ", ".join(latex_escape(str(skill)) for skill in skills)
                sections.append(f"\\section*{{Skills}}\n{skill_text}")
            continue
        entries = entries_by_section.get(section, [])
        if not entries:
            continue
        body = "\n\n".join(_render_entry(entry) for entry in entries)
        sections.append(f"\\section*{{{section_labels.get(section, section.title())}}}\n{body}")

    template_path = Path(__file__).resolve().parents[1] / "templates" / "default" / "resume.tex"
    if not template_path.is_file():
        template_path = Path(__file__).with_name("template.tex")
    template = template_path.read_text(encoding="utf-8")
    page_size = str(variant.get("page_size", "letter"))
    if page_size not in {"letter", "a4"}:
        page_size = "letter"
    values = {
        "{{PAGE_SIZE}}": page_size,
        "{{NAME}}": latex_escape(str(profile.get("name", ""))),
        "{{HEADLINE}}": latex_escape(str(variant.get("target_role") or profile.get("headline", ""))),
        "{{CONTACT}}": _render_contact(profile),
        "{{SECTIONS}}": "\n\n".join(sections),
    }
    for placeholder, value in values.items():
        template = template.replace(placeholder, value)
    return template
