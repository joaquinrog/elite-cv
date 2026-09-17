# Functional MVP Rebuild Plan

Status: proposed for review and execution

Date: 2026-09-15

## Purpose

Use the first external pilot to replace the proof-of-concept release with a
genuinely functional MVP, without copying any private participant data into the
public repository.

The pilot proved that the consent, claim review, disclosure, validation, and
deterministic build workflow can work when an agent follows the skill. It also
proved that the current product is not a usable MVP: it can render targeting
metadata as a false professional identity, report a misleading pass, ignore the
requested locale, omit stored contact data, flatten useful skill structure,
require hours of installation recovery, and produce a visually mediocre CV.

This plan is intentionally broader than a corrective patch. Intermediate phases
may land as internal checkpoints, but the product should not be presented as a
functional MVP until every release gate in this document passes.

## Product Decision

Do not release the pilot PDF. Preserve it only in the participant's private
workspace as a baseline.

Rebuild the public product first, using synthetic fixtures. After the complete MVP
passes its automated and visual test matrix, install that version in the existing
private workspace and rebuild from the already reviewed claims. The participant
should then compare the old and new PDFs and approve or reject the result.

Do not publish a narrow correctness release and call it the new MVP. Correctness,
whole-document evidence boundaries, locale, installation, structured skills,
contact control, and acceptable visual quality are all MVP requirements. They
remain separate implementation phases so failures can be attributed, not because
the later phases are optional.

## Functional MVP Definition

A new user with an existing CV and a supported local coding agent must be able to:

1. Understand and approve the privacy boundary.
2. Let the agent bootstrap an isolated supported toolchain without administrator
   privileges, global package managers, or undocumented recovery work.
3. Convert source material into reviewable claims and structured profile data.
4. Distinguish current identity from a target role.
5. Approve factual content and disclosure before it is rendered.
6. Build a localized, one-page, readable PDF with clean extracted text.
7. See meaningful skill groups instead of a flat keyword list.
8. Control which contact fields appear.
9. Inspect an evidence report whose claims match its actual coverage.
10. Receive a visually credible CV that is suitable for professional use.

If any step requires an improvised renderer, silent inference, misleading
validation result, or multi-hour undocumented repair, the MVP has not met its
definition.

The happy path must not require Homebrew, `sudo`, global PATH edits, manual
virtual environments, direct YAML editing, LaTeX knowledge, or individual TeX
package installation. Advanced contributors may use those tools, but ordinary
users should never need to know they exist.

## North-Star User Experience

The intended user should be able to say, in substance:

> Use Elite CV Builder to create a CV for this target role from this document,
> which contains my confirmed achievements, education, skills, and experience.

The user should not need to understand YAML, claim IDs, LaTeX, Python packaging,
Poppler, or the internal workspace layout. Those remain inspectable implementation
details, not required product knowledge.

### Required journey

1. The user attaches a supported source document and provides a target role or job
   description.
2. The skill asks once for hosted-processing consent and separately records which
   identity and contact fields may be shared.
3. Local intake extracts the document, creates source records, maps factual
   statements to claims, builds the structured profile, and proposes a variant.
4. When the owner states that the source document contains confirmed facts, the
   product offers a concise batch approval of source-backed claims. Conflicts,
   unsupported enhancements, and sensitive disclosures remain excluded or require
   explicit attention.
5. The product asks only questions that block factual correctness or materially
   affect the selected CV. Missing metrics and optional enrichment are reported
   after the build rather than turning intake into an interview.
6. The deterministic pipeline validates, builds, checks extracted text, and
   inspects the preview.
7. The user receives the PDF plus a concise summary. Evidence, audit, and manifest
   artifacts remain available for inspection without dominating the experience.
8. Release or publication still requires explicit final visual approval.

### Interaction budget

For a clean, internally consistent document whose owner grants batch approval,
the normal path should require no more than:

- One initial request containing source, target, locale, consent, and disclosure
  choices.
- One concise approval or correction checkpoint.
- One final delivery response.

The agent may ask additional questions only for conflicts, unsupported claims it
proposes to add, ambiguous identity, or missing information required by the chosen
variant.

The default response should summarize decisions rather than dump commands, claims,
or logs. Full provenance remains available in private reports.

### Supported-input boundary

The MVP must define and test a small set of supported text-bearing inputs rather
than claiming universal import. At minimum, support a normal text-based PDF and a
plain Markdown or text evidence document. DOCX may be included if it can meet the
same local extraction and privacy contract. Scanned-document OCR and arbitrary
layout recovery remain out of scope until tested separately.

### Setup budget

On a supported clean environment, the user must not need to debug packaging or
repair dependencies. Setup must complete through one documented agent-managed
path, with costs and system changes disclosed before execution.

Happy-path targets for the first supported platform:

- No administrator privileges or global package manager.
- No global PATH edits or editable Python install.
- No manual terminal commands by the profile owner.
- At most one agent-managed bootstrap action.
- At most 300 MB of downloads unless the user explicitly accepts more.
- No more than 10 minutes from approved setup to ready intake on a normal
  connection.

If the current TeX architecture cannot meet these targets, the renderer or
packaging strategy must change. Documenting the four-hour pilot flow is not an
acceptable solution.

### Product acceptance scenario

The functional MVP must pass an end-to-end synthetic test beginning with only:

- A supported source document.
- A target role.
- A locale.
- Explicit consent and disclosure choices.

It must finish with a factual, localized, visually credible PDF and valid private
reports without manual YAML editing, direct LaTeX editing, an improvised renderer,
or terminal repair by the profile owner.

The MVP must define explicit acceptance scenarios for macOS, Linux, and Windows.
A platform may be labeled preview rather than stable, but it must never fall into
an undocumented partial workflow or require the agent to invent installation
steps.

## Platform Acceptance Scenarios

Every platform scenario starts with a clean, non-administrator user account, a
supported coding agent, a synthetic text-based PDF, a target role, locale,
consent, and contact-disclosure choices. Every scenario must end with the same
logical workspace, validation behavior, PDF, preview, private reports, and cleanup
capability.

### macOS

Primary baseline:

- Current supported macOS on Apple Silicon.
- Intel macOS is a separate packaging target and must not silently run an ARM
  binary through assumptions about Rosetta.
- No Homebrew, MacTeX, BasicTeX, Poppler, Xcode Command Line Tools, or preexisting
  project virtualenv may be assumed.
- No `sudo`, installer package, global PATH mutation, or files under
  `/usr/local/texlive` may be required on the happy path.
- Runtime and workspace data must remain under a user-controlled application,
  cache, or workspace directory with restrictive POSIX permissions.
- Gatekeeper and code-signing behavior for downloaded executables must be
  documented and tested; the agent must not instruct the user to bypass security
  controls.
- Cleanup must remove the isolated runtime and private workspace without touching
  unrelated Homebrew, Python, or TeX installations.

Acceptance test:

1. Bootstrap from the canonical agent prompt or release entrypoint.
2. Create a private workspace without manual terminal commands.
3. Intake and batch-review the synthetic source.
4. Build and inspect a one-page localized PDF.
5. Verify links, extracted text, preview, reports, and permissions.
6. Remove the isolated runtime and confirm no privileged paths were changed.

### Linux

Primary baseline:

- A documented mainstream distribution and architecture, initially Ubuntu LTS
  x86_64; Linux ARM64 is a separate artifact and test target.
- No assumption that TeX, Poppler, Python development headers, a browser, `sudo`,
  `apt`, `dnf`, `pacman`, Snap, or Flatpak is available.
- Do not mutate `/usr`, `/opt`, shell startup files, or system package databases.
- Respect XDG base directories for cache and configuration when storing the
  isolated runtime outside the private workspace.
- Apply restrictive POSIX permissions and test behavior under a non-root account.
- Detect headless environments and generate previews without a display server.
- Support paths containing spaces and non-ASCII characters.

Acceptance test:

1. Run in a clean non-root Ubuntu LTS environment without system PDF tooling.
2. Bootstrap entirely in user space.
3. Complete intake, batch review, validation, build, and visual artifact
   generation headlessly.
4. Verify PDF text, links, page count, private permissions, and XDG paths.
5. Clean up without invoking the distribution package manager.

### Windows

Primary baseline:

- Current supported Windows 11 x86_64 in native PowerShell.
- WSL, Git Bash, Chocolatey, Scoop, winget, administrator elevation, Developer
  Mode, and a system Python installation may not be assumed.
- The native Windows path is the happy path; WSL may be documented separately but
  must not be required.
- Support drive letters, backslashes, spaces, non-ASCII paths, long-path limits,
  reserved filenames, and file-locking behavior.
- Replace POSIX mode assumptions with tested Windows access controls or a clearly
  documented best available private-directory policy.
- Do not modify the machine-wide PATH, registry, execution policy, or protected
  directories.
- Executables must be signed or accompanied by a documented integrity check. The
  agent must not ask the user to disable Defender or SmartScreen.

Acceptance test:

1. Bootstrap from native PowerShell as a standard user without package managers.
2. Create the workspace under a path containing spaces.
3. Complete intake, batch review, validation, build, and preview generation
   without WSL.
4. Verify PDF text, links, page count, private-data handling, and cleanup while
   files are opened and closed normally.
5. Confirm that no registry, execution-policy, machine PATH, or protected
   directory change occurred.

### Cross-platform parity

For the same synthetic profile and variant:

- Rendered wording, section order, localized dates, selected facts, disclosure
  decisions, and evidence coverage must match across platforms.
- Minor PDF binary and font-rendering differences are acceptable only when visual
  and extracted-text checks pass.
- Manifests must record OS, architecture, runtime, renderer, and tool versions.
- Errors must use the same stable codes even when remediation guidance differs by
  platform.
- Workspace paths in reports must use safe relative references where possible.
- No platform may weaken consent, claim approval, disclosure, or public/private
  boundaries to simplify installation.

## Confirmed Findings

### P0: Target role is rendered as a factual headline

`render_latex()` currently prefers `variant.target_role` over
`profile.headline`. A role used for tailoring is therefore displayed as if the
profile owner already holds that role.

This bypasses the intended evidence boundary because headline fields are not
included in bullet traceability coverage. The pilot produced a validation pass
and 100 percent coverage while rendering an unsupported professional identity.

### P0: Coverage wording overstates its scope

`traceability_coverage` measures selected bullets only. It does not cover the
headline, contact data, skills, role names, organizations, locations, dates, or
education entries without bullets. A CV with no bullets currently reports 100
percent coverage.

### P0: Locale is stored but ignored

Section labels and `Present` are hardcoded in English. Dates are rendered as raw
`YYYY` or `YYYY-MM` values. The LaTeX template does not configure language-aware
typesetting.

### P0: Doctor does not check the complete template toolchain

The default template requires `enumitem`, but `elitecv doctor` does not check for
it. The pilot passed the documented checks and then failed its first build due to
the missing package.

### P0: Extracted-text quality is not validated

The build checks only that extracted text is non-empty. Automatic LaTeX
hyphenation produced split words in the extracted text. There were no replacement
characters or Unicode noncharacters in the pilot, but the output was still poor
for search and ATS-style text processing.

### P1: Skills lose their useful structure

`profile.skills` is an unconstrained flat array and the renderer joins every item
with commas. Disciplines, methods, tools, and languages become one undifferentiated
line. Skills also have no claim links.

### P1: Stored contact fields are silently omitted

The private profile stored phone and location, but `_render_contact()` renders
only email and links. The schema does not define the contact object precisely
enough to make the mismatch visible.

### P1: The default presentation is functionally valid but visually weak

The authentic build is readable and one page, but it has generic typography,
weak use of vertical space, limited hierarchy, and no visual character suitable
for a design candidate.

### P1: Installation is too expensive for casual adoption

The successful pilot required multiple Python installation recoveries, Homebrew,
BasicTeX, Poppler, a TeX package update, a manual `enumitem` install, elevated
commands by the user, approximately 1.5 GB including caches, and more than four
hours end to end.

### P2: `check-public` usage is easy to misunderstand

The command correctly fails against a private workspace. Its intended target is
a clean public candidate tree, but the CLI and primary workflow do not make that
scope sufficiently obvious.

## Goals

- Never render a target role as an attained role by default.
- Make coverage claims precise and impossible to mistake for whole-document
  provenance.
- Produce correctly localized Spanish and English output.
- Detect every required build dependency before compilation.
- Preserve useful skill categories and their evidence links.
- Render approved contact fields consistently.
- Improve the default visual result without harming text extraction, privacy, or
  one-page behavior.
- Reduce the supported installation path to a documented, reproducible flow.
- Turn the pilot failures into synthetic regression tests.
- Extend the evidence boundary beyond bullets so every rendered professional
  assertion has approved provenance or an explicit owner-controlled disclosure
  contract.
- Complete a second external-pilot build that the profile owner considers both
  factually accurate and professionally usable.

## Non-Goals For This Update

- Perfect native import for every PDF or DOCX layout. A guided supported intake
  path is in scope; universal document parsing is not.
- A hosted editor or hosted database.
- A theme marketplace.
- ATS scoring or interview guarantees.
- Automatic approval of claims or disclosures.
- Cryptographic proof against a malicious actor.
- Copying private pilot files, text, names, contact details, hashes, or reports
  into the public repository.

## Implementation Sequence

Each phase must pass before the next phase begins. Correctness changes must not be
mixed with visual redesign or renderer changes in the same patch, but every phase
through the private pilot replay is required for the functional MVP.

## Phase 0: Onboarding Architecture And Synthetic Regression Baseline

Record the current time-to-first-CV and select the distribution boundary before
implementing packaging. Evaluate a standalone CLI release, a normal wheel inside
an agent-managed environment, an ephemeral tool runner, and a repository
bootstrap entrypoint. Reject any primary path that requires an editable install,
system Python mutation, Homebrew, or routine elevated privileges. Record license,
download size, platform coverage, update behavior, and cleanup behavior.

Create a fictional Spanish-language junior design profile that reproduces the
product conditions without reproducing the participant's identity or wording.

The fixture must include:

- A factual profile headline that differs from the target role.
- An `es-MX` variant.
- Current and single-month entries.
- Phone, location, email, and two links.
- Groupable design, research, tool, and language skills.
- Long Spanish words near likely line boundaries.
- Approved claims for every rendered bullet.
- A target role that must remain internal metadata.

Add baseline tests that fail against the current implementation for the confirmed
bugs. Do not add the broken pilot PDF as a fixture.

Acceptance criteria:

- The fixture contains fictional data only.
- A test proves that the current target role incorrectly replaces the factual
  headline before the fix.
- Tests cover Spanish labels, date formatting, contact rendering, grouped skills,
  dependency checks, and extracted-text quality.
- One primary installation and invocation contract is selected.
- The baseline records setup steps, manual interventions, elapsed time, download
  size, and first-build result without retaining private user content.

## Phase 1: Factual Rendering Contract

### 1.1 Separate targeting metadata from displayed identity

For this update, render `profile.headline` under the name. Keep
`variant.target_role` in private build metadata and reports, not in the visible
CV.

Do not introduce a variant-specific display headline in the first fix. If future
pilots demonstrate a need, add a separate field with explicit claim IDs and owner
approval rather than reusing `target_role`.

Acceptance criteria:

- A target role different from the profile headline never appears under the name.
- The manifest and evidence report continue to record the target role.
- A regression test uses two visibly different synthetic strings.
- Existing English synthetic examples render their factual profile headline.

### 1.2 State the current coverage scope accurately

Keep the existing manifest field for persisted artifact compatibility, but change
human-facing CLI and report labels to `Bullet traceability coverage`.

Add explicit manifest metadata describing the scope, for example:

```json
{
  "traceability_coverage": 1.0,
  "traceability_scope": "selected_bullets"
}
```

Do not describe this value as whole-document provenance. Define and test the
zero-bullet behavior explicitly. Prefer `not applicable` in human-facing output
instead of presenting vacuous 100 percent coverage as a quality signal.

This is an immediate truth-in-reporting correction, not the final MVP provenance
model. Phase 4 must add evidence or explicit owner control for other rendered
professional assertions before the final MVP gate.

Acceptance criteria:

- CLI, audit report, evidence report, and documentation name the bullet-only
  scope.
- A zero-bullet fixture does not present a misleading human-facing 100 percent.
- Existing manifests remain readable.

### 1.3 Document the authentic-build claim

Update `AGENTS.md`, the portable skill, and the README:

- `Generated with Elite CV Builder` requires a successful `elitecv build`.
- Reading the repository or borrowing its principles is not execution.
- An unsupported renderer must not be substituted after a dependency failure.
- A blocked build must be reported as blocked.

Add agent evals for these behaviors.

## Phase 2: Locale And Text Integrity

### 2.1 Introduce a small locale layer

Support `en-US` and `es-MX` explicitly. Reject or warn on unsupported locales
instead of silently rendering mixed-language output.

The locale layer must control:

- Section labels.
- `Present` versus `presente`.
- Month labels.
- Year, month, and day precision.
- Single-date entries, which must not repeat the same start and end value.
- Date-range punctuation.

Keep raw ISO dates in structured data and localize only at render time.

Acceptance criteria:

- `2025-10` to `2025-10` renders as one localized month.
- An open-ended `2026-08` entry renders with the localized current label.
- English fixtures remain English.
- Spanish fixtures contain no hardcoded English section or date labels.

### 2.2 Make typesetting language-aware

Evaluate two implementations against the synthetic fixture:

1. Locale-aware LaTeX language support.
2. Suppressed automatic hyphenation with layout adjustments.

Choose the smallest option that preserves readable line wrapping, clean extracted
text, and a manageable BasicTeX dependency set. Any new required package must be
added to `doctor` in the same change.

Acceptance criteria:

- Known synthetic Spanish words are not split into `word-\ncontinuation` in
  `pdftotext -layout` output.
- No replacement characters or Unicode noncharacters occur.
- The PDF has no text outside the page and no overfull boxes.
- Any accepted underfull-box warnings are documented and bounded.

### 2.3 Strengthen PDF text checks

Replace the current non-empty-only check with a text-quality audit that reports at
least:

- Empty or implausibly short extraction.
- Replacement characters and Unicode noncharacters.
- Missing expected identity and section text.
- Unexpected line-end hyphenation in protected fields such as headline,
  organization, education, and skills.

The audit must avoid logging raw private text in public or routine terminal
output.

## Phase 3: Friction-Free Runtime, Doctor, And Installation

### 3.1 Check the actual template contract

Centralize the default template's required LaTeX files and have `doctor` check all
of them with `kpsewhich`:

- `article.cls`
- `inputenc.sty`
- `fontenc.sty`
- `lmodern.sty`
- `geometry.sty`
- `hyperref.sty`
- `enumitem.sty`
- Any locale or typography package added in Phase 2 or Phase 5

Acceptance criteria:

- A missing `enumitem.sty` fails `doctor` before build.
- Unit tests mock each missing tool and package.
- Guidance identifies whether the missing dependency belongs to Poppler, TeX, or
  Python.
- `doctor` and build use the same dependency inventory.

### 3.2 Provide machine-readable diagnostics

Add `elitecv doctor --json` without removing the human-readable output. Agents
should receive stable check IDs, status, category, and remediation guidance.

On the happy path, `doctor` is an internal preflight run by bootstrap and build,
not a troubleshooting assignment handed to the profile owner. Missing optional
capabilities must not block intake and review.

### 3.3 Ship one isolated bootstrap path

Reproduce the editable-install failure in a Codex-like environment, but do not
make editable installation part of the user journey. The primary runtime must be
self-contained or installed only inside an agent-managed isolated directory.

Test implementation paths in order:

1. A standalone release artifact with no user-managed Python.
2. A normal wheel in an agent-managed isolated environment.
3. An ephemeral tool runner only if it materially reduces prerequisites.

Editable installation remains a contributor workflow only.

Acceptance criteria:

- The user quickstart does not depend on editable-install machinery.
- Python version requirements are checked before installation instructions.
- Offline failure and required network access are reported clearly.
- The primary path stays inside one removable app or workspace directory.
- macOS ARM64 instructions disclose download size and cleanup before approval.
- No user-managed PATH change or elevated operation occurs on the happy path.

### 3.4 Deliver a self-contained supported build path

Evaluate self-contained renderer and PDF-inspection options against license,
binary size, platform support, determinism, text extraction, links, preview
generation, and typography. Typst, Tectonic, a packaged browser path, or another
local renderer may be considered; no candidate wins merely because it installs
easily.

Make an explicit ship or reject decision. A new renderer is acceptable only if it
passes the same PDF, text, page-count, report, and privacy tests and records its
identity in the manifest.

The evaluation does not block Phases 1 and 2, but a self-contained build path that
meets the setup budget is a final MVP gate. Keeping TeX and Poppler is acceptable
only if they can be isolated and meet the same budget; global installation is not
the fallback.

### 3.5 Test clean-environment onboarding

Automate disposable acceptance runs for the stable platform matrix:

- macOS Apple Silicon.
- Ubuntu LTS x86_64.
- Windows 11 x86_64 in native PowerShell.

Each starts without global project dependencies and must bootstrap, run preflight,
perform synthetic intake, build, and clean up. Record user actions, privilege
prompts, download size, elapsed time, files written outside the isolated
directory, and cleanup result. Intel macOS and Linux ARM64 remain explicit
additional packaging targets rather than assumed compatibility.

## Phase 4: Whole-Document Evidence Model, Skills, And Contact

This is a deliberate MVP-level schema change. The current single schema version
applies to sources, claims, profile, and variant together, so design the version
transition for the complete document set rather than changing only
`profile.schema.json`. The runtime must either validate the JSON Schemas or make
the executable validation contract explicitly authoritative; schemas must not
remain decorative documentation that can diverge from runtime behavior.

Because the public project is still alpha, prefer a clear schema-version
increment and migration documentation over a loose dual-format renderer. Update
`init`, loaders, executable validation, all schemas, synthetic examples, reports,
and tests in the same phase. Convert the known private pilot workspace only
outside the public repository.

### 4.1 Add guided intake and concise review

Expose one agent-owned intake operation accepting source path, target role or job
description, locale, consent, and contact disclosure choices. The user must not
create or edit workspace YAML manually.

The operation must register and fingerprint the source, extract it locally,
create pending source-backed claims and profile fields, exclude unsupported
enhancements, detect conflicts, prioritize questions, and propose a variant
without presenting its target as current identity.

Support a recorded batch decision when an owner confirms that the source contains
accurate self-attested facts. Store the source fingerprint, affected claim IDs,
reviewer, timestamp, and disclosure decision. Batch approval must never approve
unsupported or conflicted claims, and contact requires a separate explicit choice.

Question priorities:

- `blocking`: required for correctness or build.
- `recommended`: materially improves this CV without blocking it.
- `optional`: enrichment shown after delivery.

Acceptance criteria:

- A clean source requires no manual YAML editing.
- A consistent source can be approved in one concise checkpoint.
- The checkpoint shows selected content and sensitive disclosure, not every
  internal record.
- Optional metrics and links do not prevent a truthful first build.
- Full decisions remain inspectable in private reports.

### 4.2 Extend provenance beyond bullets

Define evidence linkage for rendered professional assertions, including at
minimum:

- Display headline.
- Entry role or title, organization, and dates.
- Education credentials.
- Skill items.

Identity and contact fields require owner control and disclosure but do not need
to pretend to be independently verified claims. Reports must distinguish factual
provenance from disclosure authorization.

Acceptance criteria:

- Targeting metadata can never satisfy evidence requirements for a visible field.
- Every visible professional assertion is linked to eligible claims.
- Owner-controlled identity and contact fields have explicit disclosure state.
- Reports separately state bullet coverage, structured-field coverage, and
  disclosure checks; no aggregate percentage hides an uncovered category.
- A document with no bullets cannot obtain a misleading whole-document pass.

### 4.3 Replace flat skills with evidence-linked groups

Target structure:

```yaml
skill_groups:
  - id: skills.design
    label: Design and prototyping
    items:
      - name: Interactive prototypes
        claim_ids: [claim.synthetic.prototyping]
  - id: skills.tools
    label: Tools
    items:
      - name: Figma
        claim_ids: [claim.synthetic.figma]
```

Requirements:

- Stable group IDs.
- Human-authored localized labels.
- Item-level claim IDs.
- Variant-level group selection or exclusion.
- Validation that every rendered skill references release-eligible claims.
- Compact rendering with one labeled row per group.
- No skill-level proficiency claims unless evidence supports them.

Acceptance criteria:

- Design capabilities, research methods, tools, and languages render as distinct
  groups.
- Irrelevant groups remain in the master profile but can be excluded by a
  variant.
- Skills contribute to a separately reported structured-field provenance check.
- Flat comma-soup output is removed.

### 4.4 Define and render contact fields

Specify the contact schema rather than accepting arbitrary properties. Support:

- Email.
- Phone.
- Location.
- Labeled links.

Contact disclosure must remain an explicit, machine-verifiable owner decision.
Use a variant allowlist or field-level disclosure records; merely storing a field
must never cause it to appear. Apply the same rule to existing email and links,
not only newly rendered phone and location.

Acceptance criteria:

- Stored and approved phone and location are rendered.
- Missing optional contact fields do not create stray separators.
- Links remain active and extracted text remains readable.
- Tests use fictional contact information only.

## Phase 5: Default Template Quality

Begin only after factual rendering, locale behavior, and structured skills are
stable.

### Design direction

- Professional editorial layout rather than decorative portfolio styling.
- Sans-serif typography available within the supported toolchain.
- Strong but restrained hierarchy suitable for design and technical roles.
- Compact metadata and dates.
- Clear labeled skill groups at the bottom.
- Better use of vertical space for short profiles.
- No columns that damage reading order.
- No icons required to understand contact information.
- No gradients, heavy decoration, or graphics that weaken text extraction.

### Responsive content-density strategy

Do not stretch text merely to fill a page. Define bounded layout profiles for
short, medium, and dense content using controlled spacing and typography. Content
selection remains the primary way to fit a page.

### Visual test matrix

Build synthetic fixtures for:

- Short junior profile.
- Medium one-page profile.
- Dense one-page profile.
- Spanish and English.
- Letter and A4.

Acceptance criteria:

- One-page targets remain one page.
- No clipping, overlap, or overfull boxes.
- Extracted reading order matches visual order.
- Section hierarchy and skill groups remain clear at actual size.
- Short profiles do not leave an obviously unfinished lower half.
- Human review rates the new synthetic and private pilot outputs above the
  baseline for clarity, credibility, and visual fit.

## Phase 6: Workflow And Safety Documentation

Update the public workflow after the implementation stabilizes:

- Provide a staged prompt for hosted coding agents: consent, intake, owner review,
  validation, build, visual review, and optional release.
- Explain that a GitHub URL does not install or activate a skill.
- Require agents to report whether the skill was installed natively or followed
  manually.
- Prioritize blocking questions separately from optional enrichment questions.
- State that missing results should remain open questions, not fabricated claims.
- Clarify that `check-public` targets a clean public candidate tree, not a private
  workspace.
- Add the expected negative result when scanning a private workspace.
- Provide a guided intake command or equally concrete agent workflow for an
  existing PDF. It may rely on agent-assisted extraction in this MVP, but it must
  create pending claims and questions without treating source bullets as approved
  facts.
- Publish one canonical starter prompt and one concise approval prompt.
- Define supported agent/platform combinations and fail honestly on unsupported
  clients instead of improvising a partial workflow.
- Keep normal delivery focused on the PDF, key decisions, blocking issues, and
  release status. Detailed commands and traces belong in private reports.

Add agent evals for:

- A direct `read this repository and optimize my CV` request.
- Missing `pdflatex` or a required TeX package.
- Pressure to use ReportLab after a failed build.
- A target role different from the candidate's current identity.
- Spanish output.
- Unsupported tool-to-task associations.
- A request to guarantee ATS success.

## Phase 7: Integrity Verification, Deferred

After the correctness release, consider output hashes and an `elitecv verify`
command. Describe this as artifact integrity, not proof against a malicious actor.

Potential scope:

- Hash PDF, preview, extracted text, evidence report, and audit report.
- Recheck input hashes.
- Confirm renderer and tool versions.
- Confirm page count and bullet coverage.
- Detect post-build modification.

This phase does not block the pilot rebuild.

## Test Plan

### Unit tests

- Headline selection and target-role isolation.
- Locale labels and date formatting.
- Single-month date behavior.
- Contact rendering and separator handling.
- Skill-group schema and rendering.
- Claim eligibility for rendered skill items.
- Zero-bullet coverage presentation.
- Complete doctor package inventory.
- Text-quality issue classification.

### Integration tests

- Build Spanish letter PDF.
- Build English A4 PDF.
- Extract text and assert localized expected content.
- Assert internal target metadata is absent from visible text when it differs from
  the factual headline.
- Assert links, phone, and location are present when approved.
- Assert manifest records target role, locale, renderer, and coverage scope.
- Assert missing required TeX package fails in `doctor` before compilation.
- Exercise path handling with spaces and non-ASCII characters on every stable
  platform.
- Run native Windows tests without WSL path translation.
- Run Linux preview generation in a headless environment.
- Verify platform-specific private-directory controls.
- Compare normalized extracted text and manifest semantics across platforms.

### Security and privacy tests

- Keep all fixtures synthetic.
- Run `check-public` on the repository candidate.
- Confirm no private workspace paths or pilot identifiers enter tracked files.
- Confirm diagnostics do not print raw private source excerpts.

### Visual verification

- Render all fixture previews.
- Compare old and new synthetic previews.
- Review at full-page and actual-size scales.
- Record findings against a short visual rubric rather than treating page count as
  proof of quality.

## Internal Delivery Milestones

These milestones are sequencing boundaries, not separately marketable MVP
releases. The functional MVP is complete only after Milestone D and all release
gates.

### Milestone A: Runnable correctness foundation

- Synthetic regression fixture.
- Factual headline rendering.
- Accurate bullet-coverage wording.
- Locale labels and dates.
- Complete doctor checks.
- Text-integrity checks.
- Agent contract and critical evals.
- Primary bootstrap and runtime architecture decision.

### Milestone B: Complete content and disclosure model

- Whole-document provenance contract.
- Structured, evidence-linked skills.
- Contact schema and rendering.
- Schema-version decision and migration notes.
- Guided intake, batch approval, and prioritized questions.

### Milestone C: Usability, visual quality, and installation

- Default template redesign.
- Density fixtures and visual rubric.
- Supported installation quickstart.
- Supported renderer decision and implementation.
- Guided intake path.
- Clean-environment onboarding test within the setup and interaction budgets.

### Milestone D: Private pilot replay

- Install the updated public build in the existing private workspace.
- Migrate only the private profile fields required by the new schema.
- Rebuild from the same owner-approved evidence.
- Preserve the original pilot output for comparison.
- Ask the profile owner to review factual identity, language, skills, contact,
  visual quality, and release readiness.
- Do not release without explicit final approval.

## Release Gates

The update is not complete until:

- All automated tests pass.
- Public safety scanning passes on the repository candidate.
- No target role is rendered as an attained role without an explicit,
  evidence-linked display field.
- Every rendered professional assertion passes its category's provenance check.
- Every rendered identity or contact field passes explicit disclosure checks.
- Spanish output contains no English template labels.
- `doctor` detects every required template dependency.
- Extracted text passes the new quality checks.
- Skills render in meaningful groups with eligible evidence.
- Approved phone and location render correctly.
- The synthetic visual matrix passes review.
- The private pilot rebuild is reviewed by the profile owner.
- A clean supported environment reaches build without undocumented dependency or
  packaging recovery.
- The happy path requires no Homebrew, `sudo`, global PATH changes, manual YAML,
  or profile-owner terminal repair.
- A consistent source reaches build with at most one concise approval checkpoint.
- The primary supported platform meets the 10-minute and 300-MB setup targets, or
  an explicitly reviewed exception documents why a larger self-contained runtime
  is necessary.
- macOS Apple Silicon, Ubuntu LTS x86_64, and native Windows 11 x86_64 each pass
  their clean-environment acceptance scenario or are explicitly labeled preview
  with the missing gate documented before release.
- Stable-platform manifests and normalized PDF text pass cross-platform parity
  checks.

## Decisions For Review

Resolve these before implementing the affected phase:

1. Should zero selected bullets report `not applicable` or zero percent in human
   output?
2. Should Spanish typesetting use a new language package or suppress automatic
   hyphenation to keep the toolchain smaller?
3. What is the smallest coherent schema-version transition that covers all four
   documents and the known private-workspace migration?
4. Should contact authorization use field-level disclosure records or a variant
   allowlist?
5. Which supported user installation path should be primary: wheel in a venv,
   `pipx`, or `uv tool`?
6. Which renderer path meets the MVP installation gate without weakening
   deterministic output or text quality?
7. Which of macOS Apple Silicon, Ubuntu LTS x86_64, and Windows 11 x86_64 are
   stable at launch versus explicitly labeled preview?
8. Should batch approval be implemented as a CLI command, a structured agent
   operation, or both?
9. Are Intel macOS and Linux ARM64 launch requirements or post-MVP packaging
   targets?

## Success Measures

- A new user reaches a valid build without undocumented recovery steps.
- A normal user starts with one natural-language request and never edits YAML or
  runs setup commands manually.
- Clean macOS, Linux, and Windows environments complete their declared support
  scenario within the stated interaction and setup budgets.
- `doctor` catches missing dependencies before build.
- No visible factual field is populated from targeting metadata.
- Human-facing coverage language matches what is actually measured.
- Spanish output is consistently Spanish and extracts cleanly.
- The profile owner can scan skills by category rather than parse a flat list.
- The private pilot rebuild is judged factually accurate and materially better
  looking than both previous outputs.
- End-to-end pilot time and manual interventions are substantially lower on the
  next clean environment.
- Detailed evidence remains available without overwhelming the default user
  response.
