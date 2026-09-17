# Visual Review & Bullet Quality Rubric

Review each short, medium, and dense preview at actual size for both locales and
paper sizes. This rubric is separate from page-count verification.

## Visual Review Criteria
- **Clarity:** name, headline, contact, sections, dates, and skills are identified without guesswork.
- **Credibility:** restrained sans-serif typography, consistent alignment, and no decorative noise.
- **Hierarchy:** name and section headings lead; entries, dates, and bullets have distinct but quiet roles. In the Projects section, the project/artifact name is the primary bold anchor.
- **Reading order:** content reads top-to-bottom and left-to-right without columns, overlaps, or stranded labels.
- **Actual-size readability:** body text, dates, links, and skill rows remain comfortable at printed size.
- **Completeness:** short layouts do not look unfinished; dense layouts do not feel cramped or clipped.

## Elite Bullet Quality Rubric (8 Dimensions)
Every technical bullet proposed by an agent must be evaluated against this rubric. Bullets should avoid generic job descriptions ("Worked on...", "Built features...").

| Dimension | 0 (Reject) | 1 (Acceptable) | 2 (Elite) |
|---|---:|---:|---:|
| **Clear action** | Vague ("assisted", "worked on") | Partially clear | Specific engineering action verb |
| **Technical depth** | Generic | Some stack details | Architecture / systems / protocol depth |
| **Scale** | None | Implied | Quantified (nodes, models, QPS, records) |
| **Outcome** | None | Qualitative | Quantified / verifiable impact |
| **Ownership** | Unclear / passive | Partial team attribution | Clearly scoped individual ownership |
| **Baseline / comparison** | None | Implicit | Explicit before/after or benchmark ratio |
| **Relevance** | Weak / outdated | Adjacent | Directly relevant to target role |
| **Interview value** | Low / conversational | Moderate | Creates rigorous technical discussion |

## Decision Hierarchy (5 Levels of Quality)
A CV cannot be correctly optimized by a single scalar score (`bullet_score >= 12`). Elite CV Builder evaluates evidence through a 5-level hierarchy:

1. **Level 1 — Truth:** Never invent, extrapolate, or embellish facts. Every claim must be defensible in a rigorous technical interview.
2. **Level 2 — Safety & Confidentiality:** Never pressure for or expose proprietary client names, internal spend, undisclosed business volumes, or private infrastructure.
3. **Level 3 — Domain-Relevant Evidence:** Use metrics when publicly appropriate, and deep architectural/systems detail when confidential. Demand domain-appropriate outcomes, not vanity metrics.
4. **Level 4 — Role Relevance:** Directly target the technical core of the target role, discarding administrative filler.
5. **Level 5 — Presentation & Parsing:** Strict action verbs, clean typography, ATS parsing safety, zero hyphenation artifacts, and disciplined one-page budget.

## Dual Evidence Routes (Confidentiality-Aware Standards)
Metrics are evidence, not a dogma. Professional bullets must **never** be forced to leak proprietary, client, or unreleased data merely to boost a rubric score.

### Route A — Public / Quantifiable Evidence (Personal Projects / Research / Open Systems)
For personal, research, or openly measurable work, prefer at least one defensible domain-relevant measure: scale, baseline comparison, performance, accuracy, latency, cost, throughput, memory, tokens, reliability, workflow reduction, test coverage, adoption, or another technically meaningful outcome.
`Action + System + Domain-Relevant Metric/Scale + Measured Outcome`
*(Target score: 12–15 / 16).*

### Route B — Confidentiality-Aware Technical Evidence (Production / Corporate Work)
Mandatory for enterprise work under NDA or confidential business contexts:
`Action + System + Architecture/Complexity + Ownership + Engineering Consequence`
*(Target score: 10–13 / 16. Scores on Outcome or Baseline can be 0 or 1 if substituting robust engineering constraints, reliability policies, or telemetry architecture instead of confidential business metrics).*

## Content Debt vs Rewrite Debt
- **Rewrite Debt:** Unclear phrasing, passive voice, missing domain context, or formatting flaws. Solved through editing.
- **Content Debt:** Projects or experiences that are structurally sound but still maturing technically (e.g. newly founded organizations). Do **not** attempt to "solve" content debt with inflated copywriting. Mark it as content debt and update the bullet only when real engineering deliverables (compute, hardware integration, perception, telemetry) land.

## Displacement Policy (Coursework & Secondary Evidence)
Keep coursework or introductory credentials only while unused page budget exists. The moment stronger engineering evidence (production achievements, research outcomes, benchmarks) becomes available, coursework must be displaced before cutting any strong technical bullets.

## Anti-Leak Rules
Never encourage disclosing or inferring:
- Private client names or contract values
- Internal spend or private model billing
- Proprietary dataset volumes or undisclosed usage
- Unreleased architectures, credentials, or internal endpoints
When metrics are private, describe the architectural mechanism and technical consequence safely.

---
Record pass, concern, or block for each criterion and note the variant ID. A human
visual review remains required before release.
