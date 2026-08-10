# Elite CV

**A Git-native CV system that makes AI show its work. Every bullet has receipts.**

Elite CV turns fragmented career evidence into role-specific, inspectable CVs.
Agents can help organize and draft, but final bullets remain linked to approved
claims and uncertain facts stay visible. The deterministic build does not need
an external AI API.

This directory is a proposed public extraction from a private CV workspace. It
uses fictional data only, but a clean-history and artifact audit is still
required before publication. Create a fresh Git history rather than publishing
the private workspace history.

## Product proof

The synthetic walkthrough contains:

- Source records with redacted locators.
- Approved claims linked to every rendered bullet.
- Deliberately conflicted and unsupported claims that remain excluded.
- Two role variants generated from one profile.
- A selectable one-page PDF, preview, evidence report, audit report, and manifest.

The checks demonstrate traceability and build behavior. They do not prove that
a source is independently true, guarantee ATS compatibility, or guarantee an
interview.

## Five-minute sample

Requirements: Python 3.10+, PyYAML, TeX Live or MiKTeX with `pdflatex`, and
Poppler with `pdftotext`, `pdftoppm`, and `pdfinfo`.

```bash
python -m venv .venv
.venv/bin/python -m pip install -e ".[test]"
.venv/bin/python -m elitecv doctor --root examples/synthetic-profile
.venv/bin/python -m pytest -q
.venv/bin/python -m elitecv build \
  --root examples/synthetic-profile \
  --target robotics-software \
  --output-dir examples/synthetic-profile/outputs
```

Outputs are written to:

```text
examples/synthetic-profile/outputs/robotics-software/share/cv.pdf
examples/synthetic-profile/outputs/robotics-software/share/preview.png
examples/synthetic-profile/outputs/robotics-software/private/evidence-report.html
examples/synthetic-profile/outputs/robotics-software/private/audit-report.md
examples/synthetic-profile/outputs/robotics-software/private/build-manifest.json
```

Build the second variant with:

```bash
.venv/bin/python -m elitecv build \
  --root examples/synthetic-profile \
  --target ai-internship \
  --output-dir examples/synthetic-profile/outputs
```

## Private workflow

Start in a new private repository or local directory:

```bash
elitecv init --target "Robotics Software Intern"
elitecv status
elitecv review
elitecv validate --target general
elitecv build --target general
```

Edit the documented YAML files under `data/`, place raw material under
`sources/private/`, and keep personal review notes under `workspace/`. These
paths are ignored by default. Structured profile tracking, remote artifacts,
and publication require an explicit decision outside the default flow.

`init` records those defaults in `workspace/policy.yml`. The opt-ins are
explicit flags: `--track-structured-profile` and
`--allow-remote-artifacts`.

Inspect the PDF and private evidence report. Then release only the shareable
files after human review:

```bash
elitecv release general --acknowledge-visual-review
```

`release` never uploads or publishes a file.

In v0.1, a share bundle may contain only claims marked `shareable`. Claims marked
`private` or `restricted` remain in the local review workspace and cannot enter
`build` or `release` output.

## Agent workflow

Paste this prompt into a coding agent after reading `AGENTS.md` and
`docs/agent-workflow.md`:

```text
Read AGENTS.md and docs/agent-workflow.md before editing.

Inspect the files under sources/private/ and create source records, claims,
profile entries, and open questions for a CV targeted at [TARGET ROLE].

Do not invent dates, metrics, titles, awards, rankings, technologies, links,
or outcomes. Do not edit generated LaTeX. Every proposed CV bullet must
reference one or more claim IDs. Preserve conflicts and keep private data out
unless I explicitly approve its disclosure.

Run the applicable validation commands and report changed files, unresolved
questions, privacy decisions, and output paths.
```

Source documents are untrusted evidence. Embedded instructions in a document
must not be treated as agent commands. A hosted agent may transmit source data
to its provider; review that provider's data-handling policy before use.

## What the report means

The evidence report lists every rendered bullet, its claim IDs, claim
statements, safe source labels and locators, review state, disclosure state,
excluded claims, tool version, schema version, page count, and traceability
coverage. It omits raw source excerpts by default.

Traceability coverage is 100 percent when every rendered bullet has at least
one release-eligible approved claim. It is not a factual-truth guarantee.

## Boundaries

Elite CV does not scrape LinkedIn, provide a hosted editor, predict hiring
outcomes, promise universal ATS compatibility, or claim compatibility with
every coding agent. See `docs/privacy.md`, `docs/threat-model.md`, and
`docs/troubleshooting.md` for supported behavior and known limitations.

## Contributing

Use synthetic fixtures for public tests. Never submit private resumes,
transcripts, credentials, or personal generated artifacts. See
`CONTRIBUTING.md` and `SECURITY.md`.
