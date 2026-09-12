# CLI contract

```text
metriccue validate PERFORMANCE [--config CONFIG] --json
metriccue analyze PERFORMANCE [--content CONTENT] [--production PRODUCTION] [--config CONFIG] [--output RUNS]
metriccue findings RUN_DIR --json
metriccue report RUN_DIR --format markdown
```

Exit codes: 0 success; 1 unexpected failure; 2 arguments/configuration; 3 blocking data; 4 valid run without sufficient findings; 5 report failure. Exit code 4 is not a crash: explain that the data supports no reliable finding.

Never read a `.partial` run. Do not reconstruct missing output with an ad hoc calculation; report the missing capability.
