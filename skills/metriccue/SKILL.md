---
name: metriccue
description: Use when diagnosing content-operations CSV data, investigating content metric changes, or turning MetricCue evidence into evidence-linked experiment proposals.
---

# MetricCue

Use MetricCue as the sole calculation layer. The core rule is: **no number without a `finding_id`; no explanation disguised as a fact.**

## Workflow

1. Establish the business objective, metric meanings, counter mode, and input paths.
2. Run `metriccue validate PERFORMANCE --json` before analysis. Exit code 3 stops the workflow; explain repairs from `validation.json`.
3. Run `metriccue analyze PERFORMANCE` with the supplied `--content`, `--production`, `--config`, and `--output` arguments.
4. Read only `manifest.json`, `validation.json`, and `evidence.json` from the completed run. Do not inspect or send raw rows unless the user explicitly asks for local data debugging.
5. State facts and signals using the engine's values, confidence, limitations, and `finding_id`. 不得重新计算、修改或升级置信度。
6. Label business explanations as hypotheses. Generate experiment cards only from cited findings.
7. Ask for confirmation before writing experiment task files.

## Hard Boundaries

- Do not replace the CLI with pandas, spreadsheets, shell aggregation, or mental arithmetic, even as a “cross-check.” Fix or report a CLI limitation instead.
- Send aggregate evidence to a model, never raw data. Sensitive-field warnings block model handoff.
- Never turn association into causation or invent platform-algorithm explanations and industry benchmarks.
- 不得执行发布、投放、群发、删除内容或登录外部平台。Prepare proposals only.

Read [references/cli.md](references/cli.md) for command handling, [references/evidence.md](references/evidence.md) before interpreting results, and [references/experiment-card.md](references/experiment-card.md) when experiments are requested.
