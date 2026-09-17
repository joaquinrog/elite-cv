# Wave 5A Renderer Decision Experiment

Generated from synthetic fixtures only. Paths are intentionally omitted or relative.

## Measured environment

- Host evidence: `Linux-6.17.0-40-generic-x86_64-with-glibc2.39` / Python `3.12.3`
- **current-tex-poppler**: elitecv current renderer
- **tectonic**: missing_tool
- **typst**: missing_tool

## Results

| Candidate | Fixture | Status | Pages | Text | Target role absent | Repeatable |
| --- | --- | --- | ---: | --- | --- | --- |
| current-tex-poppler | short | pass | 1 | pass | True | False |
| current-tex-poppler | medium | pass | 1 | pass | True | False |
| current-tex-poppler | dense | pass | 1 | pass | True | False |
| tectonic | short | blocked | unknown | fail | True | False |
| tectonic | medium | blocked | unknown | fail | True | False |
| tectonic | dense | blocked | unknown | fail | True | False |
| typst | short | blocked | unknown | fail | True | False |
| typst | medium | blocked | unknown | fail | True | False |
| typst | dense | blocked | unknown | fail | True | False |

## Decision

Current TeX/Poppler is the only measured passing candidate in this environment. Typst and Tectonic remain blocked when unavailable; no platform, size, or license claim is inferred.

## Limits

- Budget gate is recorded as criteria only: <=300 MB artifacts and <=10 minutes per build.
- Links are checked as PDF annotations through `pdfinfo -url`.
- License and native macOS/Windows measurements remain pending.
