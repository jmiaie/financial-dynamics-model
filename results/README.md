# Results Convention

Keep only small reproducible summary artifacts in this tree.

## Directories
- `results/synthetic/`
- `results/temporal_validation/`
- `results/walk_forward/`
- `results/benchmarks/`
- `results/historical_regimes/`

## Required metadata fields
Each CSV, JSON, or Markdown artifact should record:
- model or config version
- data period
- universe
- methodology
- timestamp
- `synthetic` or `historical` tag

Avoid committing large raw datasets, notebooks with hidden state, or outputs that cannot be regenerated from repository code and documented inputs.
