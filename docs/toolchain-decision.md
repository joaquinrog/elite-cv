# Portable PDF Toolchain Decision

The prototype uses the widely available local toolchain `pdflatex` (or
`latexmk` when installed), `pdftotext`, `pdftoppm`, and `pdfinfo`.

## Decision

Use LaTeX plus Poppler for `v0.1`.

## Tradeoffs

- **Installation size:** larger than a single binary such as Tectonic, but
  common on Linux, macOS, and Windows through TeX distributions.
- **Offline behavior:** fully local after dependencies are installed.
- **Typography:** mature packages and predictable ATS-readable text output.
- **Security:** shell escape is disabled and profile values are escaped; TeX
  and PDF parsers remain third-party dependencies.
- **Reproducibility:** input hashes and tool versions are recorded; exact PDF
  bytes can still vary by TeX distribution and font package.
- **Preview and extraction:** Poppler provides the required text and image
  checks without an external service.

Tectonic remains a future comparison. It is not silently substituted when a
required dependency is missing; `elitecv doctor` reports the installation step.
