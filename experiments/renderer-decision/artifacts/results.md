# Wave 5A Renderer Decision Experiment

Generated from synthetic fixtures only. Paths are intentionally omitted or relative.

## Measured environment

- Host evidence: `Linux-6.17.0-40-generic-x86_64-with-glibc2.39` / Python `3.12.3`
- **current-tex-poppler**: elitecv current renderer
- **tectonic**: Tectonic 0.17.0
- **typst**: typst 0.15.1 (9dfd3a08)

## Results

| Candidate | Fixture | Status | Pages | Text | Target role absent | Repeatable |
| --- | --- | --- | ---: | --- | --- | --- |
| current-tex-poppler | short | pass | 1 | pass | True | False |
| current-tex-poppler | medium | pass | 1 | pass | True | False |
| current-tex-poppler | dense | pass | 1 | pass | True | False |
| tectonic | short | pass | 1 | pass | True | True |
| tectonic | medium | pass | 1 | pass | True | False |
| tectonic | dense | pass | 1 | pass | True | True |
| typst | short | pass | 1 | pass | True | False |
| typst | medium | pass | 1 | pass | True | True |
| typst | dense | pass | 1 | pass | True | True |

## Decision

Current TeX/Poppler is the only measured passing candidate in this environment. Typst and Tectonic remain blocked when unavailable; no platform, size, or license claim is inferred.

## Limits

- Budget gate is recorded as criteria only: <=300 MB artifacts and <=10 minutes per build.
- Links are checked as PDF annotations through `pdfinfo -url`.
- License and native macOS/Windows measurements remain pending.
