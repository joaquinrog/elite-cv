# Contributing

Keep changes small and tied to a reproducible behavior, test, or documented
decision.

- Use fictional or explicitly authorized public fixtures only.
- Add a failing test before production behavior changes.
- Preserve schema versioning and release gates.
- Keep generated LaTeX out of the source-of-truth workflow.
- Run `python -m pytest -q`, the relevant `elitecv build` command, and
  `elitecv check-public` before opening a pull request.
- Explain any new dependency, workflow permission, or privacy tradeoff.

Claims in documentation must be labeled as behavior, measured evidence, or
future targets. Do not use unrelated maintainer metrics as product proof.
