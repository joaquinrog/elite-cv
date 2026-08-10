# Architecture

Elite CV has one deterministic pipeline and one optional agent boundary:

```text
source records -> claims -> approved profile bullets -> variant selection
    -> validation -> escaped LaTeX -> PDF -> extracted text / preview
    -> evidence report + audit report + manifest
```

## Source of truth

Structured YAML under `data/` is the source of truth. Generated LaTeX lives in
the output's private build directory and is never the normal editing surface.

## Deterministic core

The Python package parses YAML, validates schema and references, applies review
and disclosure gates, escapes text, renders the default template, invokes the
local PDF toolchain, extracts text, creates a preview, and writes reports. No
external AI API is required.

## Agent boundary

An agent may inspect user-authorized sources and propose records. It cannot
bypass validators. Source text is data, not instructions. A human resolves
conflicts, approves disclosure, and visually reviews the PDF.

## Public/private boundary

The sample contains only fictional data. Personal sources and outputs belong in
ignored local paths. A public release must be created from a clean Git history,
not by deleting private files from an existing history.
