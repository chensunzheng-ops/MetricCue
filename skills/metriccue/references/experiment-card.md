# Experiment card

Each proposal contains:

```yaml
title: concise behavior under test
evidence:
  finding_ids: [required]
hypothesis:
  statement: causal possibility, explicitly unverified
  confidence: copied or lower than source evidence
  limitations: [required]
design:
  audience: defined segment
  control: current behavior
  variant: one focused change
  controlled_variables: []
measurement:
  primary_metric: one metric
  guardrail_metrics: []
  minimum_observations: integer
  observation_window_days: integer
decision_rule:
  adopt: measurable condition
  reject: measurable condition
  extend: insufficient or unstable result
risks: []
```

Do not claim randomization when platform distribution is uncontrolled. Propose two to four experiments, ordered by evidence strength and execution cost.
