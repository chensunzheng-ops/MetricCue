# MetricCue Design Specification

Date: 2026-09-12  
Status: Approved design, pending written-spec review  
License target: MIT

## 1. Purpose

MetricCue is a local-first, evidence-first diagnostic tool for content-operations data. It converts CSV exports into reproducible data-quality checks, metric analyses, anomaly findings, contribution analyses, charts, and testable experiment proposals.

The project is built first as a useful open-source tool. Its public repository should explain the problem, method, limitations, and results without framing the project as an interview or portfolio exercise.

## 2. Target Users and Primary Job

The initial users are individual content operators and small content teams without a dedicated data analyst.

Their primary job is:

> Given exported content and production data, identify the most important performance or workflow problems, understand which segments contribute to them, and define a small number of experiments that can validate plausible explanations.

The first release focuses on diagnosis rather than collection or execution.

## 3. Product Principles

1. Every numerical statement must be traceable to deterministic analysis output.
2. Facts, signals, hypotheses, and proposed experiments are distinct result types.
3. Missing or poor-quality data must reduce confidence or block unsupported analysis.
4. The core product must work without an LLM or external API.
5. Raw input stays local by default. AI receives aggregate evidence only.
6. Correlation is never presented as causation.
7. The initial product remains narrow enough to release and maintain.

## 4. Scope

### 4.1 Included in v0.1.0

- CSV ingestion with YAML column mapping.
- One required performance table and two optional enrichment tables.
- Validation with error, warning, and informational severities.
- Daily and cumulative counter modes.
- Metric calculation and funnel analysis.
- Robust trend and anomaly detection.
- Content-lifecycle alignment.
- Segment comparison and anomaly-contribution analysis.
- Production-cycle and workflow-efficiency analysis.
- Structured evidence, Markdown reports, and SVG charts.
- Offline rule-based recommendations.
- An optional Codex-compatible skill that turns evidence into experiment cards.
- A deterministic synthetic case study and golden tests.
- Windows and Ubuntu CI.

### 4.2 Explicitly Excluded from v0.1.0

- Platform login, scraping, or real-time APIs.
- Automatic publishing, messaging, advertising, or other external writes.
- Online accounts, collaboration, permissions, or hosted dashboards.
- Viral-content prediction.
- Unsupported causal claims.
- Enterprise attribution and cross-channel identity resolution.
- Multiple embedded model-provider integrations.

## 5. Delivery Approach

MetricCue uses a deterministic Python analysis core, a Typer CLI, and a separate skill layer.

- Python owns validation, calculations, diagnostics, confidence, and evidence.
- The CLI is the stable public interface to the analysis engine.
- The skill orchestrates CLI use and converts evidence into explanations and experiments.
- A future web interface may use the same CLI or Python API but is not part of v0.1.0.

## 6. End-to-End Data Flow

```text
CSV files + YAML configuration
        |
        v
Input identification and column mapping
        |
        v
Data validation and privacy checks
        |
        v
Canonical typed datasets
        |
        v
Deterministic analysis engine
  - metrics and funnels
  - trends and anomalies
  - lifecycle alignment
  - segment comparison
  - contribution analysis
  - production efficiency
        |
        v
Structured evidence JSON
        |
        +--> Markdown and SVG report
        |
        +--> rule-based recommendations
        |
        +--> optional skill-generated experiment cards
```

Each run is immutable and records input hashes, configuration hashes, tool version, data coverage, enabled modules, skipped modules, and validation status.

## 7. Input Contracts

### 7.1 Performance Table

`performance.csv` is required. Each row represents one content item on one date.

Required dimensions:

- `date`
- `content_id`
- `platform`
- `account_id`

At least one supported metric must be present:

- `impressions`
- `views`
- `clicks`
- `likes`
- `comments`
- `saves`
- `shares`
- `completed_views`
- `follows`
- `leads`
- `orders`
- `revenue`

The unique key is `platform + account_id + content_id + date`.

The configuration declares one counter mode per input:

- `daily`: values are increments for the date.
- `cumulative`: values are counters as of the date and are converted to increments after sorting.

Mixed counter modes are unsupported. A cumulative counter decrease is reported as a reset or backfill issue and is not silently repaired.

### 7.2 Content Table

`content.csv` is optional. Each row represents one content item.

Required when the table is supplied:

- `content_id`
- `platform`
- `account_id`
- `published_at`

Optional attributes:

- `content_type`
- `topic`
- `duration_seconds`
- `campaign`
- `author`
- `title`
- `tags`

Titles and author names are excluded from model-bound evidence by default.

### 7.3 Production Table

`production.csv` is optional. Each row represents one content production cycle.

Supported fields:

- `content_id`
- `idea_started_at`
- `brief_completed_at`
- `draft_completed_at`
- `review_started_at`
- `review_completed_at`
- `scheduled_at`
- `published_at`
- `revision_count`
- `production_cost`

This table enables production-cycle duration, review wait, publication delay, on-time rate, revision, and cost analysis.

### 7.4 Column Mapping

YAML maps source-specific column names to canonical fields. Platform-specific mappings remain configuration, not special cases in the core engine.

```yaml
data:
  counter_mode: cumulative
  timezone: Asia/Shanghai

columns:
  date: 数据日期
  content_id: 笔记ID
  impressions: 曝光数
  views: 观看数
  likes: 点赞数
  saves: 收藏数
```

## 8. Metric Definitions

Default derived metrics are calculated only when their required numerator and denominator exist:

- click-through rate = `clicks / impressions`
- view rate = `views / impressions`
- interactions = `likes + comments + saves + shares`
- engagement rate = `interactions / views`
- completion rate = `completed_views / views`
- follow conversion = `follows / views`
- lead conversion = `leads / clicks`
- order conversion = `orders / leads`
- average order value = `revenue / orders`

Denominators are configurable. A zero denominator produces a missing result with an explicit reason, never infinity or a silently substituted zero.

Metric semantics remain platform-scoped. Absolute values from platforms with different definitions are not compared by default.

## 9. Validation

Validation issues have three severities:

- Error: prevents trustworthy execution.
- Warning: permits execution but reduces confidence or skips a module.
- Info: documents coverage and non-critical limitations.

Blocking examples:

- Duplicate unique keys.
- Unparseable required dates.
- Missing platform, account, or content identifiers.
- Mixed grains or counter modes.
- Aggregate account data presented as content-level observations.

Warning examples:

- Missing optional values.
- Insufficient history or sample size.
- Cumulative counter resets.
- Content observations dated before publication.
- Inconsistent percentage scales.
- Funnel relationships that are implausible under the configured semantics.

When data is inadequate, MetricCue produces the validation report but refuses unsupported findings.

## 10. Analysis Model

### 10.1 Default Windows

- Current window: latest seven complete calendar days.
- Baseline window: preceding 28 complete calendar days.
- Incomplete current-day data is excluded by default.
- Same-weekday comparison is enabled by default.
- Shortened windows are allowed only with reduced confidence and an explicit limitation.

### 10.2 Content Lifecycle

Content is aligned by age since publication (`Day 0`, `Day 1`, and so on). A two-day-old item is compared with historical items at the same age, not with mature cumulative totals.

Outputs include 24-hour, three-day, and seven-day performance where coverage allows, along with same-age median baselines.

### 10.3 Anomaly Detection

Detection combines:

1. Configurable business thresholds.
2. Robust statistics based on median, MAD, or IQR.
3. Persistence across multiple observations.
4. Agreement across related metrics.
5. Data-quality penalties.

Small samples fall back to simple descriptive rules and low-confidence language. Viral outliers do not define the central baseline.

### 10.4 Contribution Analysis

Anomalies are decomposed by available dimensions:

- platform
- account
- content type
- topic
- duration bucket
- publication time
- campaign
- author
- lifecycle stage

The analysis distinguishes within-segment performance changes, mix shifts, volume changes, and data artifacts. Opposing aggregate and segment trends trigger a possible Simpson's-paradox warning.

### 10.5 Segment Comparison

Each segment result records sample size, median, interquartile range, baseline difference, effect size, and data coverage. Small-sample winners appear only as observations, not general rules.

### 10.6 Production Efficiency

When production data exists, MetricCue evaluates production time, review wait, publication delay, on-time publication, revision count, cost, and their associations with content outcomes. Efficiency gains are not treated as successful when performance guardrails materially degrade.

## 11. Evidence and Confidence

All findings are serialized before report generation. A finding contains:

- stable `finding_id`
- result level
- metric and direction
- current and baseline values
- absolute and relative changes
- sample size
- segment filters
- confidence level
- supporting evidence
- limitations

Result levels are:

- Fact: directly demonstrated by the data.
- Signal: a stable relationship or contribution pattern.
- Hypothesis: a plausible business explanation not established by the data.
- Proposed experiment: a procedure to test a hypothesis.

Confidence is `high`, `medium`, or `low`. It is determined from sample size, effect magnitude, persistence, data quality, and segment stability. MetricCue does not emit uncalibrated numerical probabilities.

## 12. Reports and Recommendations

Each run produces:

```text
runs/<timestamp>/
  manifest.json
  validation.json
  evidence.json
  recommendations.json
  report.md
  charts/
```

The Markdown report contains:

1. Executive summary.
2. Data health.
3. Core metrics.
4. Anomaly contribution.
5. Content insights.
6. Production efficiency.
7. Proposed experiments.
8. Limitations.

Offline recommendations map detected problem types to candidate actions. They remain proposals and never claim guaranteed impact.

## 13. Experiment Cards

The optional skill converts supported findings into experiment cards containing:

- referenced finding IDs
- hypothesis and confidence
- known limitations
- audience and content scope
- control and variation
- controlled variables
- primary metric
- guardrail metrics
- minimum observations and observation window
- adopt, reject, and extend rules
- operational risks

Priority uses a transparent simplified ICE score:

```text
priority = expected impact * evidence confidence / execution cost
```

Each component is scored from one to five with written justification. Users may override suggested priority.

## 14. Skill Contract and Safety

The skill uses public CLI commands only:

```text
metriccue validate <files> --json
metriccue analyze <files> --output <run-dir>
metriccue findings <run-dir> --json
metriccue report <run-dir> --format markdown
```

The skill must:

1. Establish the user's business objective and metric semantics.
2. Run validation before analysis.
3. Stop on blocking validation errors.
4. Read only manifest, validation, and evidence outputs by default.
5. Preserve engine-calculated values and confidence.
6. Mark all business explanations as hypotheses.
7. Ask for confirmation before writing experiment task files.
8. Never perform platform writes, publishing, messaging, or advertising.

Every number in model-written output references a finding ID. Unsupported dimensions, industry benchmarks, or claims about platform algorithms are prohibited.

## 15. Privacy

- Raw source files remain local.
- Aggregate evidence is the only default model input.
- Titles, bodies, authors, and account names are excluded by default.
- Email, phone, and likely personal-identifier detection blocks model handoff and warns the user.
- Explicit user opt-in is required to include content text.
- Logs must not contain secrets, environment variables, or raw rows.

## 16. CLI Experience

Initial commands are:

```text
metriccue init
metriccue validate <performance.csv>
metriccue analyze <performance.csv> [--content ...] [--production ...] [--config ...]
metriccue findings <run-dir> --json
metriccue report <run-dir> --format markdown
```

Exit codes are stable:

- `0`: success
- `1`: unexpected application error
- `2`: CLI argument or configuration error
- `3`: blocking input-data error
- `4`: analysis completed without sufficient evidence for findings
- `5`: report-generation failure

Run output is staged before publication so partial failures cannot resemble complete runs. Completed validation and evidence artifacts remain available when later report generation fails.

## 17. Code Architecture

```text
src/metriccue/
  cli/
  config/
  ingestion/
  validation/
  metrics/
  diagnostics/
  evidence/
  reporting/
skills/metriccue/
examples/synthetic_xhs/
tests/unit/
tests/integration/
tests/golden/
docs/
.github/workflows/
```

Typed models define interfaces between modules:

- `MetricDefinition`
- `ValidationIssue`
- `AnalysisContext`
- `Finding`
- `Limitation`
- `ExperimentCard`
- `RunManifest`

CLI, JSON, and reports share these models so their semantics cannot diverge independently.

## 18. Synthetic Golden Case

The repository includes a synthetic, Xiaohongshu-style account with approximately 90 days and 180 content items. It intentionally contains:

1. A recent increase in videos longer than 60 seconds and a decline in their completion rate.
2. Tutorial content with high save rate but low follow conversion.
3. One viral outlier that inflates mean views without improving the median.
4. Review wait increasing from roughly one to three days and delaying time-sensitive content.
5. Missing content tags and one cumulative-counter reset.

Expected behavior is recorded in `expected_findings.yaml`. MetricCue must detect the planted issues, avoid claiming unrelated high-confidence problems, reduce confidence when tags are missing, separate mix shift from within-segment decline, and produce two to four focused experiment proposals.

## 19. Testing and CI

Unit tests cover mapping, type conversion, counter conversion, formulas, zero denominators, anomaly statistics, lifecycle alignment, contribution calculations, confidence, and privacy detection.

Integration tests cover the complete three-table flow, optional-table degradation, Windows and Linux paths, Chinese headers and labels, UTF-8, corrupted inputs, invalid configuration, and no-model operation.

Golden tests verify:

- planted findings are detected
- unrelated findings are not high confidence
- report values equal evidence values
- fixed inputs produce stable core findings
- charts contain no blank data, NaN, or infinity

CI runs Python 3.11 through 3.13 on Ubuntu and Windows, Ruff, type checking, pytest, package building, golden report generation, and example-output privacy checks.

Core calculation modules target at least 90% test coverage; overall project coverage must be at least 80% without treating coverage as a substitute for behavioral tests.

## 20. Repository Presentation

The primary README is Chinese with a concise English summary and a separate English README. Its opening sequence is:

1. One-sentence product value.
2. Input-to-output visual.
3. Short demonstration.
4. Three-command quick start.
5. Example findings.
6. Architecture and methodology.
7. Tests, privacy, and limitations.
8. Roadmap and contribution guidance.

The repository presents MetricCue as a normal open-source product. It does not mention interview preparation or instruct readers how to evaluate the author.

Issue and pull-request templates accept bugs, platform mapping templates, and diagnostic-rule proposals. They require anonymized examples and prohibit personal customer data.

## 21. Release Acceptance Criteria

`v0.1.0` requires all of the following:

- The three-table contract and YAML mapping work.
- Validation supports error, warning, and informational issues.
- Trend, anomaly, contribution, lifecycle, and production-efficiency modules work.
- Every finding is represented in structured evidence JSON.
- Markdown and core SVG charts are generated.
- The skill produces evidence-linked experiment cards without recalculating metrics.
- Offline operation succeeds without model credentials.
- Golden tests detect all planted issues.
- Windows and Ubuntu CI pass.
- Three quick-start commands reproduce the example.
- Methodology, privacy, limitations, and contribution documentation exist.
- At least three target users complete the defined diagnostic task.

If user testing is not complete, the release is `v0.1.0-rc1`; validation is not claimed prematurely.

## 22. User Validation

Three to five content operators receive the same synthetic dataset and task:

> Identify the main source of the recent engagement decline and propose one experiment for next week.

The study records completion time, misunderstood outputs, blocked steps, proposed experiments, and whether the user can trace a conclusion to evidence. It does not solicit promotional praise.

Any public efficiency claim must use observed results. No time-saving, accuracy, or adoption percentage is written before measurement.

## 23. Development Sequence

1. Define schemas, configuration, golden data, and expected findings.
2. Implement validation and privacy checks with tests.
3. Implement metrics, lifecycle, anomaly, contribution, and efficiency analysis with tests.
4. Implement evidence persistence, reports, charts, and CLI.
5. Implement and verify the skill against public CLI behavior.
6. Add CI, documentation, user testing, and release artifacts.

## 24. Naming Decision

The working name is `MetricCue`, with repository and package identifier `metriccue`.

`OpsLens` was rejected because GitHub contains multiple active projects with that name, including evidence-first operations diagnostic tools. As of 2026-09-12, GitHub name searches and PyPI index checks found no direct `MetricCue` repository or distribution conflict. Name availability is not a trademark clearance and should be rechecked immediately before public release.

## 25. Maintenance Boundary

The maintainer commits to the stability of the core diagnostic contracts and methods. Platform mappings and additional diagnostic rules are added only in response to demonstrated use cases and may be community-contributed. The roadmap does not promise universal platform coverage or a hosted commercial product.
