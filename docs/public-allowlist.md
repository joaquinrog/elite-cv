# Public Extraction Allowlist

This directory is the proposed clean public extraction. It contains no real
profile, raw source, personal PDF, credential, cloud identifier, or private Git
history.

## Allowed paths

- `elitecv/`: generic deterministic package and CLI.
- `examples/synthetic-profile/`: fictional source, claims, profile, variants,
  and generated sample artifacts.
- `templates/`: generic ATS-oriented LaTeX template.
- `schemas/`: versioned public schema descriptions.
- `docs/`, `README.md`, `ROADMAP.md`, `AGENTS.md`, `CONTRIBUTING.md`,
  `SECURITY.md`, and `LICENSE`: public product documentation and policy.
- `.github/`: workflows that operate on synthetic data only.
- `tests/`: synthetic positive and negative fixtures.
- `requirements-ci.txt`, `.gitleaks.toml`, and `.github/dependabot.yml`:
  reviewed supply-chain controls.

## Never copy from the private workspace

- `sources/raw/` or extracted private source text.
- Root-level `sources/`, `data/`, `cv/`, or `reviews/` from the personal CV
  workspace.
- Private contact values, employer/client identifiers, URLs, credentials, or
  generated personal artifacts.
- The current repository's Git history.
- Binary artifacts outside the explicitly reviewed synthetic sample outputs.

This allowlist is a publication review aid, not proof that a file is safe.
Run `elitecv check-public`, inspect the complete fresh Git history, and review
the generated artifacts before publication.
