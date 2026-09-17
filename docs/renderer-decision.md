# Renderer decision record

Status: benchmark incomplete; production renderer unchanged

Date: 2026-09-15

## Decision criteria

The supported local pipeline must remain deterministic enough to audit, preserve
selectable text and PDF links, generate previews headlessly, support the declared
platforms, install without privileges, stay within 300 MB of downloads, and reach
a first build within 10 minutes.

## Measured evidence

The reproducible Wave 5A harness ran on Ubuntu-compatible Linux x86_64 with Python
3.12.3 using only synthetic short, medium, and dense Spanish fixtures.

- The current TeX/Poppler pipeline built all three fixtures as one-page PDFs.
- Elapsed build times were between 1.20 and 1.29 seconds in this installed
  environment. This is build time, not clean setup time.
- Extracted text passed the product audit and the target role stayed absent from
  visible text.
- PDF previews and active link annotations were produced.
- Raw PDF and preview hashes differed between identical runs. Byte-for-byte
  repeatability is therefore not established and requires normalization or a
  narrower semantic determinism contract.
- Output PDFs were approximately 95–100 KiB. This does not measure the installed
  TeX/Poppler toolchain or download budget.

Machine-readable results are under
`experiments/renderer-decision/artifacts/results.json`; the concise generated
summary is `results.md`.

## Unmeasured candidates

Typst and Tectonic were not installed. They were recorded as blocked rather than
downloaded automatically. No conclusion is made about their binary size, setup
time, licenses, text quality, links, previews, determinism, or native platform
behavior. Candidate-specific synthetic templates are also required before a fair
comparison.

## Provisional outcome

Keep TeX/Poppler as the production baseline. Do not start production renderer or
packaging migration until authorized experiments can download pinned candidate
artifacts, record checksums and licenses, and run native macOS ARM64 and Windows
11 PowerShell jobs. Ubuntu x86_64 remains the only stable candidate; macOS and
Windows remain preview targets.
