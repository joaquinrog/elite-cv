# Claim Provenance Specification

Schema version `1` is used by every structured root document.

## Source record

```yaml
schema_version: 1
sources:
  - id: source.example
    type: project-notes
    label: Redacted source label
    path: sources/private/notes.pdf
    confidentiality: private
    collected_at: 2026-01-15
    fingerprint: null
```

The path may point to an ignored local file. A source record never authorizes
publishing that source.

## Claim record

```yaml
claims:
  - id: claim.example
    statement: A concise source-supported statement.
    evidence:
      - source_id: source.example
        locator: "page:2"
        excerpt: null
    evidence_status: sourced
    review_status: approved
    disclosure: shareable
    reviewed_by: profile-owner
    reviewed_at: 2026-01-15
    questions: []
```

Evidence states are `sourced`, `self_attested`, `externally_verified`,
`unsupported`, and `conflicted`. Review states are `pending`, `approved`, and
`rejected`. Disclosure states are `private`, `shareable`, and `restricted`.

## Profile and variants

Profile entries have stable IDs and contain bullets. Each bullet has a stable ID,
text, one or more `claim_ids`, and a review state. A variant selects entries,
orders sections, and defines page size and page target.

The release validator accepts a bullet only when every referenced claim exists,
has an allowed evidence state, is approved, and has `shareable` disclosure.
`private` and `restricted` claims remain local in v0.1. Natural-language
semantic faithfulness still requires human review.
