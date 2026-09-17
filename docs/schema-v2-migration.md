# Schema v2 migration

Schema v2 changes the four workspace documents as one contract. The runtime does
not render a mixture of v1 and v2 files.

Before migrating a private workspace, create a local backup outside the public
repository. Do not copy private profile data, source excerpts, or generated
artifacts into this repository.

## Sources and claims

- Change `schema_version` to `2` in `sources.yml` and `claims.yml`.
- Keep source fingerprints, confidentiality, safe labels, and redacted locators.
- Keep dates as quoted ISO strings so YAML does not coerce them into date objects.

## Profile

- Change `schema_version` to `2`.
- Add `headline_claim_ids` with eligible claims supporting the visible headline.
- Add `claim_ids` to each entry to support its visible role, organization, and
  dates. Education entries follow the same rule.
- Replace `skills` with `skill_groups`. Each group has a stable `id`, a localized
  `label`, and items containing `name` and `claim_ids`.
- Define all contact keys: `email`, `phone`, `location`, and `links`. Use `null`
  or an empty list when an optional value is absent.

## Variant

- Change `schema_version` to `2`.
- Add `include_skill_groups` with the group IDs selected for this CV.
- Add `contact_fields` as an explicit allowlist containing any of `email`,
  `phone`, `location`, and `links`.
- Do not copy `target_role` into the profile headline. It remains private
  targeting metadata.

## Verification

Run the draft validation first, then build only after all referenced claims and
disclosure choices have been reviewed:

```bash
elitecv validate --root PATH --target VARIANT
elitecv build --root PATH --target VARIANT
```

Review the PDF, evidence report, audit report, and manifest. Publication still
requires explicit final visual approval.
