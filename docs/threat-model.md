# Threat Model

## Assets

- Personal profile and contact data.
- Raw resumes, notes, transcripts, certificates, and source documents.
- Claim states and disclosure decisions.
- Generated PDFs, reports, and build metadata.

## Threats and controls

| Threat | v0.1 control | Residual risk |
| --- | --- | --- |
| Private file is tracked | Ignore local paths; run `check-public` | Existing history or manual force-add can still leak it |
| Hosted agent receives sources | Explicit warning and agent instructions | Provider retention and account settings remain external |
| Source prompt injection is executed | Treat source text as untrusted evidence | An agent can still make unsafe proposals; deterministic gates limit release |
| LaTeX injection | Escape profile-controlled text; disable shell escape | Third-party TeX packages and toolchain remain dependencies |
| Variant releases restricted content | Strict builds accept `shareable` claims only | Human review is still required before sharing a PDF |
| Path traversal deletes or writes files | Variant IDs are validated and output paths are contained | A user can still choose an external output directory explicitly |
| Raw excerpt appears in report | Reports use labels and locators, not excerpts | A future report feature could regress without tests |
| Secret enters public tree | Pattern scan and clean-history checklist | Regex checks have false positives and false negatives |
| Malicious PDF abuses parser | Time-limited Poppler inspection and documented dependency scope | The parser is still third-party software |
| CI exposes a personal artifact | Synthetic-only workflow, pre-upload scan, protected-branch uploads | Repository owners can add unsafe workflow changes |

Security checks are guardrails, not guarantees. Review permissions, dependencies,
Actions, artifacts, and complete Git history before publication.
