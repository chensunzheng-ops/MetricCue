# Target-user test protocol

The purpose is to test whether a content, new-media, data, or strategy operator can reach an evidence-traceable diagnosis without developer assistance. Store only anonymous participant IDs such as `P01`; do not record employer, account, customer, or raw export data.

## Fixed task

Give the participant a clean environment, the repository, and the synthetic example. Use exactly this task:

> Identify the main source of the recent engagement decline and propose one experiment for next week.

Do not explain commands unless the participant becomes blocked. Start timing when the task is shown and stop when the participant presents a diagnosis and experiment.

## Observation record

```markdown
Participant ID:
Role category:
Environment and Python version:
Start/end and completion time:
Completed independently: yes/no
Blocked steps and requested help:
Interpretation errors:
Finding IDs cited correctly: yes/no
Numbers trace to evidence.json: yes/no
Association kept separate from causality: yes/no
Experiment has hypothesis, primary metric, guardrails, window, and decision rule: yes/no
Unprompted feedback (paraphrased, no identifying details):
Product correction made:
Retest result:
```

Success means the participant completes the task, cites at least one correct `finding_id`, introduces no unsupported numeric claim, and proposes a bounded experiment without presenting causality as established. Record friction even when the final answer is correct.

`v0.1.0` is withheld until at least three target users complete this protocol and resulting material issues are corrected and retested. Until then, the validated release stage remains `v0.1.0-rc1`. Do not claim measured time savings unless the completed records support that exact claim.
