# Evidence interpretation

Use the result levels literally:

- `fact`: directly observed.
- `signal`: stable relationship or contribution, not causal.
- `hypothesis`: proposed explanation requiring validation.
- `proposed_experiment`: procedure to test a hypothesis.

For every numeric sentence include the source `finding_id`. Preserve `current_value`, `baseline_value`, `relative_change`, `sample_size`, `confidence`, and limitations. If evidence is missing, say the current run cannot answer the question.

Never average precomputed row rates when the engine reports an aggregate rate. Never silently exclude outliers, missing rows, platforms, or periods.
