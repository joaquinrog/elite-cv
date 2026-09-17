# Functional MVP Execution Plan

Status: execution baseline

Date: 2026-09-15

Product specification: `docs/first-external-pilot-remediation-plan.md`

## Purpose

Turn the product rebuild plan into small, verifiable delivery waves that can be
assigned to builders without overlapping ownership or silently deciding product
contracts during implementation.

The public repository must use synthetic data only. The private pilot replay is
an owner-operated final gate and is never delegated with private material unless
the owner separately approves that provider interaction.

## Frozen Decisions

These decisions remain fixed unless an implementation experiment produces
contrary evidence and the execution plan is updated before dependent work starts.

1. Use schema version 2 for sources, claims, profile, and variant together.
2. Do not maintain a dual-format renderer. This project is alpha; document a
   deliberate v1-to-v2 migration instead.
3. `profile.headline` is the only current visible headline.
   `variant.target_role` is private targeting metadata.
4. Human output reports bullet traceability, structured-field provenance, and
   disclosure checks separately. Zero selected bullets are `not applicable`.
5. Visible professional assertions require eligible claim IDs. Identity and
   contact fields require owner disclosure authorization rather than pretending
   to be independently verified claims.
6. Skills use stable groups, localized human labels, item-level claim IDs, and
   variant-level group selection.
7. Contact rendering uses a variant allowlist for email, phone, location, and
   labeled links. Storage alone never authorizes rendering.
8. Guided intake and batch approval are domain operations exposed through the
   CLI. Unsupported and conflicted claims cannot be batch-approved.
9. Runtime validation is authoritative and JSON Schemas must have parity tests
   against it.
10. Support `en-US` and `es-MX`; structured dates stay ISO and are localized only
    at render time.
11. Renderer, PDF inspector, and previewer are separate interfaces. Typst is the
    leading candidate, not an adopted dependency, until the decision benchmark
    passes.
12. Initial release posture is Ubuntu LTS x86_64 stable, with macOS ARM64 and
    Windows 11 x86_64 preview until native clean-environment gates pass.

## Delivery Rules

- One builder owns a wave at a time when it touches `models.py`, `validate.py`,
  schemas, or shared fixtures.
- A builder starts from the current workspace, preserves unrelated changes, and
  edits only the wave's declared surface.
- Tests are written or updated before implementation behavior is changed.
- Generated files under `build/`, `dist/`, and private workspaces are not edited
  or committed.
- Every wave ends with focused tests, the full Python suite, `git diff --check`,
  and public-safety scanning when available.
- A failed gate is fixed in the same wave. Later waves do not compensate for an
  unresolved earlier contract.
- Builders return a short result containing changed files, verification, open
  issues, and no copied private or verbose tool output.

## Orchestration Budget

- Default planner: `gpt56-luna-plan`.
- Default builder: `gpt56-luna-build`.
- Small isolated fixture, documentation, and formatting work:
  `deepseek-flash-build`.
- Escalate one difficult integration to `gpt56-terra-build` only after a concrete
  Luna blocker is identified.
- Use one final `gpt56-terra-plan` read-only review; do not use Sol, fast, high, or
  max variants by default.
- Do not launch independent agents that must edit the same files. Parallel work
  is limited to isolated research, documentation, CI, or packaging surfaces after
  their contracts are frozen.

## Wave 0: Regression Baseline

Owner: `deepseek-flash-build`

Scope:

- Add one fictional Spanish junior-design fixture without pilot wording or
  identifiers.
- Add failing-then-fixed regression coverage for headline isolation, Spanish
  labels and dates, contact omission, skill grouping contract, dependency
  inventory, and extracted-text classification.
- Record the current renderer/toolchain baseline without claiming unsupported
  cross-platform measurements.

Primary files:

- `examples/`
- `tests/unit/test_render.py`
- `tests/unit/test_validation.py`
- `tests/unit/test_cli.py`
- `tests/integration/test_build.py`
- `tests/fixtures/` if a shared fixture directory is introduced

Gate:

- Existing tests still pass.
- New tests demonstrate the intended contracts without permanently asserting
  known broken behavior.
- Fixtures contain fictional data only.

## Wave 1: Factual Rendering And Locale

Owner: `gpt56-luna-build`

Scope:

- Render the factual profile headline and keep the target role private.
- Rename human-facing coverage and define zero-bullet presentation.
- Add a small `en-US` and `es-MX` locale layer for labels and dates.
- Add privacy-safe PDF text-quality classification.
- Keep the existing renderer for this correctness wave.

Primary files:

- `elitecv/render.py`
- `elitecv/validate.py`
- `elitecv/build.py`
- `elitecv/report.py`
- relevant unit and integration tests

Gate:

- Target role is absent from extracted visible text when it differs from the
  factual headline.
- Spanish fixtures have no English template labels.
- Single-month and open-ended dates are localized correctly.
- Reports and manifests describe bullet-only coverage honestly.
- Existing English fixtures remain stable.

## Wave 2: Diagnostic Contract

Owner: `gpt56-luna-build`

Scope:

- Centralize the active template dependency inventory.
- Make `doctor` and build consume the same inventory.
- Add `doctor --json` with stable IDs, categories, status, and safe remediation.
- Distinguish required build capabilities from optional intake capabilities.

Primary files:

- `elitecv/cli.py`
- `elitecv/build.py`
- a small shared diagnostics module if needed
- `tests/unit/test_cli.py`
- integration tests for missing dependencies

Gate:

- Every active template dependency is checked before compilation.
- Each missing dependency produces a stable machine-readable result.
- Diagnostics do not emit source excerpts or private absolute paths.

## Wave 3: Schema V2 And Evidence Model

Owner: `gpt56-luna-build`

Scope:

- Implement schema v2 across all four document types.
- Add or align the source schema and schema/runtime parity tests.
- Add claim links for headline, experience metadata, dates, education, and skills.
- Add grouped skills and variant group selection.
- Add explicit contact allowlisting and disclosure checks.
- Update reports to expose category results without a misleading aggregate pass.
- Migrate all public synthetic examples and document private migration steps.

Primary files:

- `elitecv/models.py`
- `elitecv/validate.py`
- `elitecv/render.py`
- `elitecv/report.py`
- `schemas/*.schema.json`
- public synthetic fixtures
- validation, rendering, integration, and security tests

Gate:

- All public documents use schema v2.
- Every visible professional assertion has eligible provenance.
- Contact fields render only when allowlisted.
- Flat skills are rejected and grouped skills render compactly.
- Runtime/schema parity tests pass.

## Wave 4: Guided Intake And Approval

Owner: `gpt56-luna-build`

Scope:

- Add reusable local intake and approval domain operations.
- Support text-bearing PDF and Markdown/plain-text inputs.
- Register safe source metadata and fingerprint locally.
- Generate pending source-backed claims, questions, profile data, and a proposed
  variant without treating targeting metadata as identity.
- Record batch approval with reviewer, timestamp, source fingerprint, claim IDs,
  and separate contact disclosure.
- Expose the operations through concise CLI commands.

Primary files:

- new `elitecv/intake.py` or equivalent
- new `elitecv/approval.py` or equivalent
- `elitecv/cli.py`
- `elitecv/models.py`
- `elitecv/validate.py`
- intake, security, CLI, and end-to-end tests

Gate:

- A consistent synthetic source reaches a build-ready checkpoint without manual
  YAML editing.
- Unsupported and conflicted claims remain unapproved.
- Blocking, recommended, and optional questions are distinct.
- Raw source text stays out of routine reports and public output.

## Wave 5A: Renderer Decision Experiment

Owner: `gpt56-luna-build`

Scope:

- Introduce only the minimum adapter seam needed to benchmark renderers.
- Compare current TeX/Poppler, Tectonic, and Typst using identical synthetic
  short, medium, and dense inputs.
- Measure locally available evidence for size, setup time, files written,
  cleanup, page count, links, extracted text, reading order, Unicode, preview,
  and repeatability.
- Record unknown platform measurements as pending rather than extrapolating.

Primary files:

- an isolated benchmark under `tools/` or `experiments/`
- renderer adapter boundary in `elitecv/` only if required
- synthetic benchmark fixtures
- `docs/renderer-decision.md`

Decision gate:

- Select a renderer only from measured results.
- Reject candidates that cannot plausibly meet 300 MB and 10 minutes or that
  weaken text, links, privacy, or deterministic behavior.
- If no candidate passes, stop implementation and revise the product budget or
  architecture explicitly.

## Wave 5B: Runtime And Packaging

Owner: `gpt56-terra-build` only if the selected packaging integration exceeds
Luna's demonstrated capacity; otherwise `gpt56-luna-build`.

Scope:

- Implement the selected renderer, inspector, and previewer adapters.
- Package a checksummed, isolated, removable runtime.
- Add platform detection, safe installation, cleanup, manifest metadata, and
  stable errors.
- Never modify global PATH, shell startup files, registry, execution policy, or
  protected directories.

Primary files:

- renderer/build modules
- `packaging/` or `scripts/`
- `pyproject.toml`
- release workflow files
- installation documentation and tests

Gate:

- Ubuntu clean-environment scenario meets the declared budget.
- macOS and Windows artifacts build and run in native CI or remain explicitly
  preview with failed/missing gates documented.
- Licenses, checksums, architecture, tools, and cleanup behavior are recorded.

## Wave 6: Template And Product Workflow

Owner: `gpt56-luna-build`

Scope:

- Redesign the selected default template after content contracts stabilize.
- Add bounded short, medium, and dense layout profiles in English/Spanish and
  Letter/A4.
- Update README, workflow, portable skill, troubleshooting, and agent evals.
- Keep the default interaction to initial request, concise checkpoint, and final
  delivery for a clean source.

Gate:

- Visual fixtures have no clipping, overlap, broken reading order, or obviously
  unfinished short layout.
- All automated, security, public-safety, and supported-platform tests pass.
- A human visual rubric records clarity, credibility, hierarchy, and actual-size
  readability.

## Native CI And Release Matrix

Required jobs:

| Job | Initial status | Required evidence |
| --- | --- | --- |
| Ubuntu LTS x86_64 | stable candidate | clean bootstrap, build, text, links, preview, permissions, cleanup, budget |
| macOS ARM64 | preview candidate | native signed/checksummed artifact, Gatekeeper-safe flow, build and cleanup |
| Windows 11 x86_64 | preview candidate | native PowerShell flow, spaces/Unicode path, ACL policy, no registry/PATH changes |

Normalized wording, section order, dates, selected facts, disclosure decisions,
coverage semantics, and stable error codes must match. PDF bytes and rasterization
may differ only when visual and extracted-text gates still pass.

## Final Independent Review

Owner: `gpt56-terra-plan`, read-only.

Review:

- Product specification against implemented behavior.
- Privacy boundaries and synthetic-only public history.
- Schema/runtime parity and migration documentation.
- Renderer benchmark evidence and packaging claims.
- Full test output, public-safety result, platform evidence, and unresolved gates.

The review may block release but does not edit implementation. Builders fix any
findings in the owning wave before the review is rerun.

## Completion Boundary

Repository implementation is complete only after Waves 0 through 6 and the
independent review pass. Product release remains blocked until the owner performs
the private pilot replay, compares the previous and new outputs, approves factual
identity, locale, contact disclosure, skills, and visual quality, and explicitly
authorizes release.
