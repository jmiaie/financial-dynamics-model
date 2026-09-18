# Result Source Map

This is the traceability backbone for `TECHNICAL-PAPER.md`: for every table and number in that
document, this file (together with its machine-generated companions) states the exact source
file, exact JSON key path, and sha256 of that source file, so a reviewer can check any number in
under 30 seconds.

**This file is not hand-typed.** It is a thin index over two machine-generated outputs produced
by `scripts/generate_tables.py` directly from the committed artifacts:

- `tables/source_map.json` — 467 rows, machine-readable (`row_id`, `file`, `key_path`, `sha256`).
- `tables/source_map_full.md` — the same 467 rows as a Markdown table, for direct browsing.

Regenerate both with:
```
python publication/historical-regime-study/scripts/generate_tables.py
```
This performs no network access and reads only already-committed files under `results/`,
`configs/`, and `data/manifests/`.

## How to check a number in `TECHNICAL-PAPER.md`

1. Find the number in the paper (e.g. "FDM pipeline, holdout 2025, mean ret h1 = −0.000293").
2. Find the matching `row_id` in `tables/source_map.json` or `tables/source_map_full.md` — row
   IDs are namespaced by section: `primary.<period>.<model>.<column>` (§2 of the paper),
   `robustness.<symbol>.<period>.<column>` (§3), `sparse_cell.<index>...` (§4.1),
   `case_study.qqq_2025.*` (§4.2 / `CASE-STUDY.md`), `hash_table.*` (dataset/config hashes cited
   throughout).
3. Open the `file` at that row, navigate to `key_path`, and confirm it matches the paper's number.
4. Independently confirm the file is the one actually referenced by running
   `sha256sum <file>` and comparing to the row's `sha256`.

## Row-ID namespace reference

| Namespace prefix | Paper section | Source artifacts |
|---|---|---|
| `primary.<period>.<model>.<column>` | §2 (Primary results, SPY-v1) | `results/historical_regimes/fdm_hist_regime_v1_{dev_formation,val_2024,holdout_2025}.json` |
| `primary.<period>.<model>.regime_counts` | §2 | same three files, `models[i].regime_counts` |
| `robustness.<symbol>.<period>.<column>` | §3 (Robustness / SPY-v2) | `results/historical_regimes/fdm_hist_regime_v1_robustness_{symbol}_{period}.json`, `models[model==financial_dynamics_pipeline].key_metrics.<field>` |
| `sparse_cell.<index>.<symbol>.<period>.<model>.<regime>.h<horizon>.<method>` | §4.1 (sparse-cell disclosure) | same 15 robustness files, `models[model==<model>].bootstrap_records[<index>].block_size` |
| `case_study.qqq_2025.*` | §4.2, `CASE-STUDY.md` | `fdm_hist_regime_v1_robustness_qqq_holdout_2025.json` (+ `superseded_150_resamples/` copy for the before/after contrast) |
| `hash_table.*` | §1.1, `SOURCE-GATE.md` §4–5 | `data/manifests/yf_fd_etfs_daily_2015_2025_{v1,v2}.json`, `data/manifests/yf_fd_etfs_daily_2015_2025_v2_PROVENANCE.md`, `configs/experiments/fdm_historical_regime_study_{v1,v2_robustness}.yaml` |

## Coverage check

- §2 (primary results): 3 periods × up to 5 models × 9 numeric columns + regime counts —
  every cell in every table in TECHNICAL-PAPER.md §2.1–2.3 has a `primary.*` row.
- §3 (robustness): 5 symbols × 3 periods × 9 numeric columns — every cell in the §3 table has a
  `robustness.*` row.
- §4.1 (sparse-cell disclosure): all 174 verified rows (not a sample) are individually mapped via
  `sparse_cell.*` rows, each pointing at its exact `bootstrap_records[<index>]` entry.
- §4.2/`CASE-STUDY.md` (QQQ 2025 RISK_OFF worked example): every field quoted in the case study —
  regime count, summary record, both bootstrap methods' records, and the pre-fix 150-resample
  comparison record — has a `case_study.qqq_2025.*` row.
- Every dataset/config hash cited anywhere in this pack (`SOURCE-GATE.md`, `TECHNICAL-PAPER.md`,
  `reproducibility.json`) has a `hash_table.*` row.

**Not covered by an individual row (by design):** narrative/discussion sentences in
`TECHNICAL-PAPER.md` §5–7 that describe a *pattern across* numbers already mapped above (e.g. "no
single directional claim about FDM's volatility level holds across all three periods") are
supported by the union of the relevant `primary.*`/`robustness.*` rows already listed, not by a
separate row of their own — see `CLAIM-REGISTER.md`, which enumerates these interpretive claims
individually and points each one back to the specific rows in `tables/source_map.json` that
support it.

## Full table

See `tables/source_map_full.md` (467 rows) or `tables/source_map.json` (same data, structured).
The first 10 rows and the case-study rows are reproduced below for immediate inspection; the
remainder follows the identical schema.

| Row ID | Source file | JSON key path | sha256 |
|---|---|---|---|
| `primary.dev_formation.financial_dynamics_pipeline.self_trans` | `results/historical_regimes/fdm_hist_regime_v1_dev_formation.json` | `models[model==financial_dynamics_pipeline].key_metrics.mean_self_transition` | `81a32e5362d81d630a5fb7e34cd807399b19562ca6586f40ae63aa90c0428b35` |
| `primary.dev_formation.financial_dynamics_pipeline.mean_ret_h1` | `results/historical_regimes/fdm_hist_regime_v1_dev_formation.json` | `models[model==financial_dynamics_pipeline].key_metrics.mean_return_h1` | `81a32e5362d81d630a5fb7e34cd807399b19562ca6586f40ae63aa90c0428b35` |
| `case_study.qqq_2025.regime_counts` | `results/historical_regimes/fdm_hist_regime_v1_robustness_qqq_holdout_2025.json` | `models[model==financial_dynamics_pipeline].regime_counts.RISK_OFF` | `7af9c81baf9ee89568969323a53cfa35483a2d74580ea16f5ff532e45dbc867d` |
| `case_study.qqq_2025.summary_record` | `results/historical_regimes/fdm_hist_regime_v1_robustness_qqq_holdout_2025.json` | `models[model==financial_dynamics_pipeline].summary_records[regime==RISK_OFF,horizon==1]` | `7af9c81baf9ee89568969323a53cfa35483a2d74580ea16f5ff532e45dbc867d` |
| `case_study.qqq_2025.bootstrap_moving_block` | `results/historical_regimes/fdm_hist_regime_v1_robustness_qqq_holdout_2025.json` | `models[model==financial_dynamics_pipeline].bootstrap_records[regime==RISK_OFF,horizon==1,method==moving_block]` | `7af9c81baf9ee89568969323a53cfa35483a2d74580ea16f5ff532e45dbc867d` |
| `case_study.qqq_2025.bootstrap_stationary` | `results/historical_regimes/fdm_hist_regime_v1_robustness_qqq_holdout_2025.json` | `models[model==financial_dynamics_pipeline].bootstrap_records[regime==RISK_OFF,horizon==1,method==stationary]` | `7af9c81baf9ee89568969323a53cfa35483a2d74580ea16f5ff532e45dbc867d` |
| `case_study.qqq_2025.superseded_150_resample_moving_block` | `results/historical_regimes/superseded_150_resamples/fdm_hist_regime_v1_robustness_qqq_holdout_2025.json` | `models[model==financial_dynamics_pipeline].bootstrap_records[regime==RISK_OFF,horizon==1,method==moving_block]` | `5808f6480552b77c7eca47e480c51a0fdf1353453e0ee78a7e338d10504db8ba` |
| `hash_table.dataset_v1_canonical` | `data/manifests/yf_fd_etfs_daily_2015_2025_v1.json` | `sha256.dataset_canonical` | `91caa6cde08358091125a6576ff3f2be5666791b06df67d462c2aad6f771ada9` |
| `hash_table.dataset_v2_canonical` | `data/manifests/yf_fd_etfs_daily_2015_2025_v2.json` | `sha256.dataset_canonical` | `94ea2886772afc7adcbf070bf1563a59295c1e7b1f837e157dfe5880c5b12582` |
| `hash_table.config_v1_primary` | `configs/experiments/fdm_historical_regime_study_v1.yaml` | `(whole file sha256)` | `299b1ed0dffc77afc685721c27a261a61b6a7ef1d1a1734af2062cfba5001b16` |

(See `tables/source_map_full.md` for all 467 rows.)
