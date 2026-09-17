# Renderer decision record

Status: Wave 5B benchmark completed; candidate evaluation recorded; production renderer unchanged

Date: 2026-09-16

## Decision criteria

The supported local pipeline must remain deterministic enough to audit, preserve
selectable text and PDF links, generate previews headlessly, support the declared
platforms, install without privileges, stay within 300 MB of downloads, and reach
a first build within 10 minutes.

## Measured evidence (Wave 5B)

The reproducible Wave 5B harness ran on Ubuntu-compatible Linux x86_64 with Python
3.12.3 using synthetic short, medium, and dense Spanish fixtures across three candidates:

| Candidate | Version | Binary / Download Size | Network at build | Elapsed Time | Output PDF Size | PDF Links (`pdfinfo -url`) | Hash Repeatability |
| --- | --- | ---: | --- | ---: | ---: | --- | --- |
| **current-tex-poppler** | TeX Live 2023 | ~500 MB+ system install | None (installed) | 1.24s – 1.41s | 104 – 108 KiB | Found (100%) | Non-identical (`False`) |
| **tectonic** | 0.17.0 | 9.9 MB tar.gz (26 MB bin) | Required on 1st run | 0.54s – 0.60s | 13 – 16 KiB | Found (100%) | Identical on 2/3 (`True`) |
| **typst** | 0.15.1 | 16.6 MB tar.xz (54 MB bin) | Zero (hermetic) | 0.19s – 0.22s | 38 KiB | Found (100%) | Identical on 2/3 (`True`) |

### Key findings

1. **Typst 0.15.1**:
   - Compiles 6x faster than `pdflatex` (~0.20s vs ~1.30s).
   - Single standalone static binary of 16.6 MB download (5.5% of the 300 MB budget limit).
   - Completely hermetic and offline: does not require network access or TeX packages.
   - Text extraction, privacy audit (target role absent), and clickable links (`pdfinfo -url`) all pass.
   - Higher binary repeatability than TeX on repeated synthetic runs.

2. **Tectonic 0.17.0**:
   - Compiles in ~0.55s once cached, reusing existing LaTeX templates.
   - Downloads TeX bundles on-demand over HTTP on first run (~30–50 MB extra into `~/.cache/Tectonic`).
   - Not hermetic on first run without an explicit local bundle archive.

3. **Current TeX/Poppler baseline**:
   - Reliable and proven in local environment, but carries the heaviest installation weight (~500 MB to 1.5 GB system packages).

Machine-readable results are under
`experiments/renderer-decision/artifacts/results.json`; the concise generated
summary is `results.md`.

## Strategic Decision

- **Production Baseline (Current Release):** Retain TeX/Poppler as the production baseline for this candidate release to avoid dual-renderer complexity during immediate onboarding.
- **Architectural Path for Next Major Version:** Typst is validated as the superior alternative: it meets every budget constraint (16.6 MB vs 300 MB cap, <1s vs 10m cap), preserves 100% of link annotations and text fidelity, and eliminates system-level TeX installations entirely. Migrating the production renderer to Typst should be scheduled as the primary objective for the post-pilot roadmap.
