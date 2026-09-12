# MetricCue

[中文](README.md)

MetricCue is a local-first, evidence-first diagnostic tool for content operations. It turns exported CSV files into traceable metric signals, data-quality findings, and Markdown/SVG reports. Explanations remain hypotheses until an experiment supplies stronger evidence.

```text
performance.csv + content.csv + production.csv + metriccue.yaml
                              │
                     validate → analyze
                              │
       manifest + validation + evidence + report + SVG charts
```

The current release is `v0.1.0-rc1`. Its example is entirely synthetic and deliberately includes declining metrics, a cumulative-counter reset, missing segment metadata, an outlier, and longer review waits.

## Three-command quick start

Python 3.11–3.13 is required. Windows PowerShell and Ubuntu are CI targets.

```bash
python -m pip install -e ".[dev]"
metriccue validate examples/synthetic_xhs/performance.csv --config examples/synthetic_xhs/metriccue.yaml --json
metriccue analyze examples/synthetic_xhs/performance.csv --content examples/synthetic_xhs/content.csv --production examples/synthetic_xhs/production.csv --config examples/synthetic_xhs/metriccue.yaml --output runs
```

The command prints an immutable run directory. Read `report.md` for the summary and `evidence.json` for structured findings with stable `finding_id` values. `metriccue init`, `metriccue findings`, and `metriccue report` support template creation and later inspection.

## Scope and boundaries

A run contains a manifest with hashes and provenance, validation issues, structured evidence, a reserved recommendations file, a Markdown report, and non-empty SVG charts. Calculations stay local by default.

MetricCue does not log in to or scrape platforms, replace a warehouse, automate publishing/advertising/deletion, claim that observational associations are causal, or invent industry benchmarks. Segment comparison and mix-decomposition primitives exist in the Python package but are not yet connected to the CLI report pipeline. No time-saving claim is made before the user-test protocol produces evidence.

Never submit real customer data, secrets, phone numbers, email addresses, or other identifying information. A suspected sensitive column produces a validation warning and must block model handoff until removed or anonymized.

Read the [data contract](docs/data-contract.md), [methodology](docs/methodology.md), [privacy model](docs/privacy.md), [contribution guide](docs/contributing.md), and [user-test protocol](docs/user-test-protocol.md). The repository also includes an evidence-safe [Codex Skill](skills/metriccue/SKILL.md).

Licensed under MIT.
