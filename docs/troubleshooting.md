# Troubleshooting

## `elitecv` is not found

Install the local package or use the module form:

```bash
python -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python -m elitecv --help
```

## Doctor reports missing tools

Install Python `PyYAML`, a TeX distribution with `pdflatex`, and Poppler with
`pdftotext`, `pdftoppm`, and `pdfinfo`. The build does not silently skip these
checks.

## A claim blocks the build

Run `elitecv review`, inspect the claim and supporting source, then either
resolve it with evidence, reject it, or remove it from the selected variant.
`unsupported`, `conflicted`, `pending`, `rejected`, and disallowed disclosure
states cannot enter a strict release.

## The PDF has the wrong page count

Read the generated audit report and preview. Shorten or reorder approved
content in the structured profile or variant. Do not edit generated LaTeX.

## Hosted-agent privacy

Stop before sending source files to a hosted agent until the profile owner has
reviewed the provider's data handling terms and explicitly accepted the risk.
