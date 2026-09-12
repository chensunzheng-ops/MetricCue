# Contributing

MetricCue welcomes focused fixes, platform field mappings, diagnostic rules, documentation improvements, and synthetic test cases.

1. Open the matching issue form. Describe the operational question and expected evidence contract.
2. Use only synthetic or irreversibly anonymized reproduction data. Never include secrets or personal/customer data.
3. Install with `python -m pip install -e ".[dev]"`.
4. Add a failing behavioral test before implementation. Keep calculation logic in the package, not in the Skill.
5. Run the full local gate:

```bash
python -m ruff format --check .
python -m ruff check .
python -m mypy src/metriccue
python -m pytest --cov=metriccue --cov-report=term-missing --cov-fail-under=80
python -m build
```

New findings must have deterministic IDs, explicit levels, sample sizes, confidence, evidence, and limitations. Never label an observational relationship as causal. Platform mappings should document export locale, grain, counter semantics, timezone, and a synthetic fixture. Diagnostic rules should state false-positive risks and behavior for missing or low-quality data.

Commit messages should be small and outcome-oriented. By contributing, you agree that your contribution is licensed under the repository's MIT License.
