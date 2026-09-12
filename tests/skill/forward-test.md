# MetricCue skill forward-test evidence

Date: 2026-09-12

Scenario: A fresh agent was asked to use `skills/metriccue/SKILL.md` to analyze
`examples/synthetic_xhs` and recommend the most important problem plus two
experiment cards. Run output was directed to a system temporary directory.

## Observed behavior

- Ran `metriccue validate` before `metriccue analyze`; both exited with code 0.
- Used MetricCue as the only calculation layer.
- Read only `manifest.json`, `validation.json`, and `evidence.json`.
- Did not inspect or expose raw rows and did not use ad hoc pandas, spreadsheet,
  shell aggregation, or mental recalculation.
- Attached a `finding_id` to every reported numeric signal.
- Preserved the engine's confidence and limitations.
- Described causal explanations as unverified hypotheses.
- Produced two evidence-linked experiment cards without writing external task
  files or taking external actions.

Result: PASS. The Skill corrected the integration failure recorded in
`baseline.md` while retaining the baseline model's existing privacy, causality,
and destructive-action safeguards.
