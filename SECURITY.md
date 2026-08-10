# Security

Elite CV is local-first but not automatically safe. A private Git repository
can still expose data through access settings, history, hosted agents, logs,
artifacts, or copied reports.

## Report a vulnerability

Do not open a public issue with credentials, private source content, or an
exploitable proof of concept. Use the repository's private vulnerability-report
flow from its Security tab. If that flow is unavailable, do not attach user
data; report only a minimal, non-sensitive summary through the maintainer
contact configured in the repository metadata.

## Scope of the v0.1 controls

- `sources/private/`, `workspace/`, and `dist/` are ignored by default.
- The public workflow uses synthetic data only.
- LaTeX is built without shell escape and profile values are escaped.
- The safety scanner checks forbidden paths, unexpected binary artifacts,
  common secret patterns, private email patterns, phone-like values, and
  allowlisted sample PDF text and metadata.
- Reports omit raw source excerpts by default.
- Hosted-agent use requires a documented warning and user decision.
- Build tools have time limits, and newly initialized private workspaces use
  owner-only POSIX permissions where the platform supports them.

These are guardrails, not a complete PII scanner, sandbox, or privacy
guarantee. Review the complete public Git history before publishing.
