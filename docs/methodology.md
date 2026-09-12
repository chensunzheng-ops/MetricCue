# Methodology and interpretation

MetricCue separates four evidence levels: fact, signal, hypothesis, and proposed experiment. The RC analysis engine emits signals; a human or Skill may form hypotheses and experiments only while preserving their source `finding_id` values.

## Windows and aggregation

By default, the current window is the last 7 complete days before the run date and the baseline is the preceding 28 days. `exclude_incomplete_today` avoids comparing a partial day. When `compare_same_weekday` is enabled, the window builder aligns the baseline length to whole weeks; it does not create a causal control group.

Count metrics use the median observation in each window. Ratio metrics use ratio-of-sums, not an average of row-level percentages:

```text
rate = sum(numerator) / sum(denominator)
absolute_change = current - baseline
relative_change = absolute_change / baseline
```

Supported derived rates are click-through, view, engagement, completion, follow conversion, lead conversion, order conversion, and average order value. Zero denominators produce missing results instead of infinity.

## Signal rule and confidence

A metric becomes a signal only when the current sample reaches `minimum_contents`, the baseline is non-zero, and the absolute relative change is at least 10%. Persistence counts current-window days on the same side of the baseline.

Confidence is a transparent heuristic based on sample size, effect magnitude, persistence, and data-quality score. Fewer than 10 observations or data quality below 0.8 is low confidence. High confidence requires all four stronger conditions: at least 30 observations, at least 20% absolute relative effect, at least 3 persistent days, and data quality at least 0.95. Intermediate support is medium. Confidence is not a p-value or causal probability.

The library exposes median/MAD robust z-scores, with IQR fallback when MAD is zero. It also exposes segment comparisons, symmetric within/mix decomposition, and aggregate-reversal detection. In `v0.1.0-rc1`, these segment primitives are tested but not yet emitted by the CLI pipeline.

## Production diagnostics

Production metrics compare current and baseline medians when at least the configured minimum number of current items exist. A signal requires at least a 10% relative change. These timings and content performance are observational: simultaneous movement does not establish that workflow latency caused distribution or engagement changes.

## Reproducibility and limitations

Every run records package version, UTC run ID, input SHA-256 hashes, configuration hash, data range, modules, and issue counts. Identical inputs and configuration support auditability, but the run timestamp intentionally creates a new immutable directory.

MetricCue does not correct selection bias, platform algorithm changes, seasonality beyond configured window alignment, campaign interference, missing-at-random assumptions, or unobserved confounders. It supplies diagnostic evidence, not attribution. Treat explanations as hypotheses and define a prospective decision rule before an experiment.
