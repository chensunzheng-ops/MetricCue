# Data contract

MetricCue reads UTF-8 CSV files. Column names are canonical English identifiers; platform-specific headers can be mapped in `metriccue.yaml` under `columns`, with canonical name as the key and source header as the value. Dates that cannot be parsed become validation errors or warnings according to their role.

## `performance.csv`

Grain: one platform + account + content item + observation date.

Required dimensions: `date`, `content_id`, `platform`, `account_id`. At least one supported metric is required: `impressions`, `views`, `clicks`, `likes`, `comments`, `saves`, `shares`, `completed_views`, `follows`, `leads`, `orders`, or `revenue`.

Counts must be non-negative. Configure `data.counter_mode` as `daily` for daily increments or `cumulative` for snapshots. In cumulative mode, MetricCue differences each content series; a decrease is reported as `counter_reset` and the affected increment is left missing rather than guessed.

## `content.csv` (optional)

Join key: `platform`, `account_id`, `content_id`. `published_at` enables lifecycle checks. Optional segment fields are `content_type`, `topic`, `campaign`, `author`, and `tags`. Missing segment values reduce comparison coverage and generate a warning; they are not silently filled.

## `production.csv` (optional)

Join key: `platform`, `account_id`, `content_id`. Supported timestamps include `idea_started_at`, `brief_completed_at`, `draft_completed_at`, `review_started_at`, `review_completed_at`, `scheduled_at`, and `published_at`. Optional numeric fields include `revision_count` and `production_cost`.

Derived production measures are review wait (`review_completed_at - review_started_at`), publication delay (`published_at - scheduled_at`), total cycle (`published_at - idea_started_at`), and on-time status. Negative durations become missing.

## Configuration

```yaml
data:
  counter_mode: cumulative
  timezone: Asia/Shanghai
analysis:
  current_window_days: 7
  baseline_window_days: 28
  minimum_contents: 10
  exclude_incomplete_today: true
  compare_same_weekday: true
columns:
  impressions: 曝光数
denominators: {}
```

Unknown configuration keys are rejected. Ratio denominator overrides must name an existing numeric column. The current RC stores timestamps without applying timezone conversion; callers should normalize sources to the configured timezone before analysis.
