# Agent Skill And Plugin Status

Elite CV Builder by joaq ships a portable Agent Skills workflow at
`skills/elite-cv-builder/SKILL.md`. Its primary job is to preserve the local
privacy and claim-review workflow when an AI agent helps create a CV.

The skill guides a reviewed conversion from existing CVs and source material.
v0.1 does not include a native PDF, DOCX, LaTeX, or legacy-schema importer;
that import path is active product work. If the selected agent can read an
existing format, it may process the material after explicit owner consent and
map it into source records, claims, and profile entries. It must not treat an
existing CV bullet as an approved fact merely because it appears in the input.
Elite CV Builder itself does not upload those materials.

## Local packaging

- `.claude-plugin/plugin.json` packages the repository for local Claude Code
  plugin testing.
- `.codex-plugin/plugin.json` packages the repository for local Codex plugin
  testing.
- Both package the same portable skill; neither package includes an MCP server
  or transmits CV data to joaq.mx.

## Public distribution status

This repository is not yet listed in a public ChatGPT, Codex, or Claude
marketplace. A public listing requires separate testing, publisher identity,
listing copy, and review. Do not describe the project as an approved ChatGPT
or Claude marketplace plugin until that review is complete.

## Skill evaluation

`skills/elite-cv-builder/evals/evals.json` defines initial positive and
negative prompts. Before public submission, run the prompts with and without
the skill in each target client and confirm that it requests consent for hosted
source inspection, preserves claim IDs, and does not promise ATS outcomes.
