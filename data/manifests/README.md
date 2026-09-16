# Dataset manifests

Each frozen dataset has a JSON manifest named `{dataset_id}.json`.

## Required schema fields

See `manifest.schema.json` for the authoritative schema. Key fields:

- `dataset_id` (string)
- `source` (string, e.g. `yfinance`)
- `source_version` (string)
- `symbols` (string[])
- `interval` (string)
- `requested_start` / `requested_end_exclusive` (ISO dates)
- `actual_start` / `actual_end` (ISO dates per symbol and overall)
- `row_counts` (object symbol -> int)
- `missing_counts` (object symbol -> int; OHLCV NaNs)
- `actions` (object: dividends/splits/capital_gains flags and counts)
- `retrieval_timestamp_utc` (ISO-8601)
- `freeze_timestamp_utc` (ISO-8601 or null)
- `status` (`ACQUIRED` | `VALIDATED` | `DATA FROZEN`)
- `sha256` (object: per-file hashes + `dataset_canonical` combined hash; null until freeze)
- `parameters` (download kwargs)
- `notes` (string)

Checksums are computed **only after** validation + freeze. Do not invent hashes.
