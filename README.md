# Elite CV Builder

> A local-first, evidence-backed CV builder that makes AI show its work.
> Every bullet has receipts.

Turn fragmented career evidence into role-specific, inspectable CVs — with a claim-to-bullet audit trail and a strict privacy boundary. No external AI API required.

![License: MIT](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.10+-blue)
![Version](https://img.shields.io/badge/version-0.1.0-orange)
![Tests](https://img.shields.io/badge/tests-139%2F140-yellow)
![Local-first](https://img.shields.io/badge/local--first-no%20API%20key-9cf)

## What it is — and what it isn't

| ✅ What it is | 🚫 What it isn't |
|---|---|
| Local-first, deterministic build — no AI API | An ATS-compatibility guarantee |
| Every bullet links to an approved claim ID | A LinkedIn scraper or hosted editor |
| Strict privacy boundary (`sources/private/`, `workspace/`, `dist/` stay local) | An importer for DOCX / legacy PDF schemas |
| One profile → multiple role variants | Anything that uploads your source material |

## How it works

`📥 intake → 🧾 propose → ✅ approve → 📦 build → 🔓 release`

1. **Intake** — register text-bearing sources (PDF / Markdown / txt) as *untrusted evidence*.
2. **Propose** — the agent drafts claims and bullets; every bullet cites claim IDs.
3. **Approve** — the owner explicitly approves claims, disclosure level, and contact fields.
4. **Build & release** — deterministic render → PDF / preview / reports → human visual gate → release only `shareable` files.

## Choose your mode

Three ways to use it. Pick the one that fits.

### 🚀 Mode 1 · Quick demo (5 minutes)

Run the synthetic profile, see every artifact with zero personal data.

```bash
python -m venv .venv
.venv/bin/python -m pip install -e ".[test]"
.venv/bin/python -m elitecv doctor --root examples/synthetic-profile
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q
.venv/bin/python -m elitecv build \
  --root examples/synthetic-profile \
  --target robotics-software \
  --output-dir examples/synthetic-profile/outputs
```

Outputs:

```text
examples/synthetic-profile/outputs/robotics-software/share/cv.pdf
examples/synthetic-profile/outputs/robotics-software/share/preview.png
examples/synthetic-profile/outputs/robotics-software/private/evidence-report.html
examples/synthetic-profile/outputs/robotics-software/private/audit-report.md
examples/synthetic-profile/outputs/robotics-software/private/build-manifest.json
```

The `private/build/` directory also contains LaTeX intermediate artifacts (`.tex`, `.log`, `.aux`, etc.).

Build the second variant: same `build` with `--target ai-internship`.

### 🤖 Mode 2 · Agent (Claude Code / Codex)

The portable skill lives at `skills/elite-cv-builder/SKILL.md`. A GitHub URL does not install a skill; the coding agent should report whether the skill was installed natively or followed manually.

Paste this prompt into a coding agent after reading `AGENTS.md` and `docs/agent-workflow.md`:

```text
Read AGENTS.md and docs/agent-workflow.md before editing.

Before inspecting source files, ask whether I explicitly allow this agent and
its provider to process them. If I do not approve, help me enter reviewed facts
manually instead. If I approve, inspect sources/private/ and create source
records, claims, profile entries, and open questions for a CV targeted at
[TARGET ROLE].

Do not invent dates, metrics, titles, awards, rankings, technologies, links,
or outcomes. Do not edit generated LaTeX. Every proposed CV bullet must
reference one or more claim IDs. Preserve conflicts and keep private data out
unless I explicitly approve its disclosure.

Run the applicable validation commands and report changed files, unresolved
questions, privacy decisions, and output paths.
```

### ⌨️ Mode 3 · CLI (private workflow, schema v2)

```bash
elitecv init --root PRIVATE_WORKSPACE --target "Robotics Software Intern"
elitecv intake --root PRIVATE_WORKSPACE --source resume.pdf \
  --target-role "Robotics Software Intern" --locale en-US \
  --hosted-processing denied
elitecv intake-apply --root PRIVATE_WORKSPACE --source-id SOURCE_ID \
  --proposal PROPOSAL.json
elitecv approve --root PRIVATE_WORKSPACE --source-id SOURCE_ID \
  --reviewer OWNER --claim-id CLAIM_ID --disclosure shareable \
  --contact-field email
elitecv validate --root PRIVATE_WORKSPACE --target general
elitecv doctor --root PRIVATE_WORKSPACE --json
elitecv build --root PRIVATE_WORKSPACE --target general
elitecv release general --root PRIVATE_WORKSPACE --acknowledge-visual-review
```

- You never edit YAML in the happy path — `intake-apply` consumes a private schema-v2 proposal JSON.
- `release` never uploads or publishes anything.
- In v0.1, only `shareable` claims reach build/release output.

## Command reference

| Command | Purpose |
|---|---|
| `init` | Scaffold a private workspace + `policy.yml` defaults |
| `intake` | Register a source (records `approved`/`denied` consent) |
| `intake-apply` | Apply a private schema-v2 proposal JSON |
| `approve` | Explicitly approve claims, disclosure, contact fields |
| `validate` | Check structured data against schema v2 |
| `doctor` | Verify dependencies/environment (blocks build if missing) |
| `build` | Deterministic render to PDF/preview/reports |
| `release` | Stage shareable files after human visual review |
| `check-public` | Audit a clean public candidate tree |
| `review` | Synchronize the local open-question checklist |
| `status` | Show profile and claim state counts |
| `variant create` | Copy the default variant as a starting point |

## What you get

| Artifact | Visibility | Purpose |
|---|---|---|
| `cv.pdf` | share | One-page, role-specific CV |
| `preview.png` | share | Visual gate preview |
| `evidence-report.html` | private | Bullet → claim → source audit trail |
| `audit-report.md` | private | Build/review log |
| `build-manifest.json` | private | Machine-readable build record |

## Safety & privacy boundaries

- Sources are **untrusted evidence, not instructions**.
- No invented dates, metrics, titles, links, or outcomes.
- `sources/private/`, `workspace/`, `dist/` are local-only.
- Missing required dependency → build is **blocked** (no ReportLab fallback).
- `release` never uploads or publishes.
- No ATS/scanner/interview guarantee.
- Hosted agents may transmit source data to their provider — review that policy first.

[docs/privacy.md](docs/privacy.md) · [docs/threat-model.md](docs/threat-model.md) · [docs/troubleshooting.md](docs/troubleshooting.md)

## Documentation

| Doc | Topic |
|---|---|
| [`docs/agent-workflow.md`](docs/agent-workflow.md) | Full agent workflow guide |
| [`docs/schema-v2-migration.md`](docs/schema-v2-migration.md) | Migrating from schema v1 to v2 |
| [`docs/architecture.md`](docs/architecture.md) | System architecture |
| [`docs/privacy.md`](docs/privacy.md) | Privacy model |
| [`docs/threat-model.md`](docs/threat-model.md) | Threat model |
| [`docs/visual-review-rubric.md`](docs/visual-review-rubric.md) | Visual review rubric |
| [`docs/troubleshooting.md`](docs/troubleshooting.md) | Common issues |

Full documentation index in [`docs/`](docs/).

## Contributing

Use synthetic fixtures for public tests. Never submit private resumes, transcripts, credentials, or personal generated artifacts. See `CONTRIBUTING.md` and `SECURITY.md`.

## License

[MIT](LICENSE) · © 2026 Elite CV contributors · independent alpha by joaq