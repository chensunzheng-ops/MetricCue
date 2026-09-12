# Privacy and data handling

MetricCue is local-first: the CLI reads local CSV files and writes local run artifacts. It has no platform login, network upload, telemetry, publishing, advertising, or deletion feature.

## Before analysis

- Export only fields necessary for the diagnostic question.
- Replace account, author, campaign, and content identifiers with stable pseudonyms.
- Remove names, free-text customer content, email addresses, phone numbers, tokens, cookies, credentials, and exact customer-level events.
- Keep raw exports outside the repository. The included example is synthetic.

Validation flags column names commonly associated with phone numbers, email addresses, or real names. This is a conservative name-based check, not a complete data-loss-prevention system. A warning permits local analysis but must block any handoff to a language model until the field is removed, anonymized, or explicitly excluded.

## Sharing results

Prefer `manifest.json`, `validation.json`, `evidence.json`, and the generated aggregate report. Review row indices and small-segment labels before sharing because they can still reveal operational details. Never attach raw reproduction data to a public issue. Create the smallest synthetic dataset that reproduces the problem, and scan it for secrets and personal identifiers.

MetricCue does not encrypt files or manage retention. Users remain responsible for filesystem access, backups, deletion policy, source-platform terms, and applicable privacy law.
