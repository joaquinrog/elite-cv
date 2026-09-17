from __future__ import annotations

from datetime import datetime, timezone
from html import escape
from typing import Any

from .models import WorkspaceDocuments
from .validate import ValidationResult


def render_evidence_report(
    documents: WorkspaceDocuments,
    validation: ValidationResult,
    *,
    page_count: int,
    tool_version: str,
) -> str:
    source_by_id = {
        source.get("id"): source for source in documents.sources.get("sources", [])
    }
    rows: list[str] = []
    for trace in validation.traces:
        bullet = trace.bullet
        claim_rows: list[str] = []
        for claim in trace.claims:
            evidence = claim.get("evidence", []) or []
            evidence_labels = []
            for item in evidence:
                source = source_by_id.get(item.get("source_id"), {})
                label = source.get("label", "redacted source")
                locator = item.get("locator", "locator withheld")
                evidence_labels.append(f"{label} ({locator})")
            claim_rows.append(
                "<li><code>"
                + escape(str(claim.get("id", "")))
                + "</code>: "
                + escape(str(claim.get("statement", "")))
                + "<br><small>evidence: "
                + escape("; ".join(evidence_labels) or "not disclosed")
                + "; review: "
                + escape(str(claim.get("review_status", "")))
                + "; disclosure: "
                + escape(str(claim.get("disclosure", "")))
                + "</small></li>"
            )
        rows.append(
            "<article><h3>"
            + escape(str(bullet.get("id", "")))
            + "</h3><p>"
            + escape(str(bullet.get("text", "")))
            + "</p><ul>"
            + "".join(claim_rows)
            + "</ul></article>"
        )

    exclusions = []
    for claim in validation.excluded_claims:
        exclusions.append(
            "<li><code>"
            + escape(str(claim.get("id", "")))
            + "</code>: "
            + escape(str(claim.get("evidence_status", "unknown")))
            + " / "
            + escape(str(claim.get("review_status", "unknown")))
            + " / "
            + escape(str(claim.get("disclosure", "unknown")))
            + "</li>"
        )

    generated_at = datetime.now(timezone.utc).isoformat()
    coverage = "not applicable" if validation.selected_bullet_count == 0 else f"{validation.traceability_coverage:.0%}"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Elite CV Builder by joaq evidence report: {escape(documents.variant.get('id', ''))}</title>
  <style>
    :root {{ color-scheme: light dark; }}
    body {{ font: 16px/1.5 system-ui, sans-serif; max-width: 900px; margin: 2rem auto; padding: 0 1rem; }}
    article {{ border: 1px solid #8886; border-radius: .5rem; padding: 1rem; margin: 1rem 0; }}
    code {{ font-family: ui-monospace, monospace; }}
    small {{ opacity: .8; }}
  </style>
</head>
<body>
  <h1>Evidence report</h1>
  <p>This report contains claim metadata and redacted source locators. It does not embed raw source excerpts.</p>
  <dl>
    <dt>Variant</dt><dd>{escape(str(documents.variant.get('id', '')))}</dd>
    <dt>Target role</dt><dd>{escape(str(documents.variant.get('target_role', '')))}</dd>
    <dt>Schema version</dt><dd>{documents.variant.get('schema_version')}</dd>
    <dt>Tool version</dt><dd>{escape(tool_version)}</dd>
    <dt>Build time</dt><dd>{escape(generated_at)}</dd>
    <dt>Page count</dt><dd>{page_count}</dd>
    <dt>Bullet traceability coverage</dt><dd>{coverage}</dd>
  </dl>
  <h2>Rendered bullets</h2>
  {''.join(rows) or '<p>No bullets selected.</p>'}
  <h2>Excluded claims</h2>
  <p>Excluded claims remain in the evidence workspace and cannot enter this release.</p>
  <ul>{''.join(exclusions) or '<li>None</li>'}</ul>
  <h2>Structured-field provenance</h2>
  <ul>{''.join('<li><code>' + escape(str(item.get('path', ''))) + '</code>: '
               + escape(', '.join(str(claim_id) for claim_id in item.get('claim_ids', [])))
               + ' / eligible: ' + escape(str(item.get('eligible', False))) + '</li>'
               for item in validation.structured_provenance) or '<li>None</li>'}</ul>
  <h2>Disclosure checks</h2>
  <ul>{''.join('<li><code>' + escape(str(item.get('field', ''))) + '</code>: '
               + escape(str(item.get('allowed', False))) + '</li>'
               for item in validation.disclosure_checks) or '<li>None</li>'}</ul>
</body>
</html>
"""


def render_audit_report(
    documents: WorkspaceDocuments,
    validation: ValidationResult,
    *,
    page_count: int,
    extracted_text_path: str,
) -> str:
    status = "PASS" if validation.is_valid else "BLOCKED"
    warnings = "\n".join(f"- `{issue.code}`: {issue.message}" for issue in validation.warnings) or "- None"
    errors = "\n".join(f"- `{issue.code}`: {issue.message}" for issue in validation.errors) or "- None"
    coverage = "not applicable" if validation.selected_bullet_count == 0 else f"{validation.traceability_coverage:.0%}"
    return f"""# Elite CV Builder by joaq audit report

- Status: **{status}**
- Variant: `{documents.variant.get('id', '')}`
- Page count: `{page_count}`
## Bullet traceability

- Coverage: `{coverage}`
- Scope: `selected_bullets`

## Structured-field provenance

{chr(10).join(f"- `{item.get('path', '')}`: {', '.join(str(claim_id) for claim_id in item.get('claim_ids', [])) or 'none'}; eligible={item.get('eligible', False)}" for item in validation.structured_provenance) or '- None'}

## Disclosure checks

{chr(10).join(f"- `{item.get('field', '')}`: allowed={item.get('allowed', False)}" for item in validation.disclosure_checks) or '- None'}
- Extracted text: `{extracted_text_path}`

## Blocking findings
{errors}

## Draft warnings
{warnings}

Automated checks are guardrails. They do not prove factual truth or visual quality.
"""
