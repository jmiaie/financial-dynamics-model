# Holdout audit — FDM Directive #9 (2025 calendar year)

**Repository:** `jmiaie/financial-dynamics-model`  
**Branch:** `research/historical-regime-validation`  
**Audit date (PT):** 2026-09-15  
**Holdout window under D9:** calendar **2025-01-01 ≤ t < 2026-01-01**  
**Dataset ID:** `yf_fd_etfs_daily_2015_2025_v1`

## Verdict

**CLEAR** — no evidence that calendar-year **2025** market data was previously inspected, tuned against, or used for empirical evaluation / performance claims in this repository.

## Scope searched

| Surface | Method | Finding |
|---|---|---|
| Working tree (src, scripts, tests, docs/research, results, examples, README, PROJECT_STATUS, CHANGELOG) | recursive text search for `2025` / `holdout` | Only non-empirical hits: `CHANGELOG.md` release date `2025-05-18`; `LICENSE` copyright year `2025`. |
| Results tree | listed `results/*` | Placeholder `.gitkeep` only under `synthetic/`, `temporal_validation/`, `walk_forward/`, `benchmarks/`, `historical_regimes/`. No CSV/JSON result packs. |
| Notebooks | tree / search | **None** present in repo. |
| Research doc | `docs/research/market-regime-temporal-validation.md` | Spec only; states “Results pending reproducible historical run.” Universe mentions SPY/QQQ/IWM/TLT/GLD as configurable examples, not a frozen 2025 evaluation. |
| Live loader / demos | `data_loader.py`, CLI, examples | Convenience `period=` downloads (e.g. `1y`, `6mo`); no pinned 2015–2025 study window; no committed 2025 OOS metrics. |
| GitHub code search | `2025` / holdout / SPY period in this repo | No empirical 2025 evaluation artifacts indexed. |

## Classification rules applied

- **CLEAR:** holdout calendar window not used for model selection, hyperparameter tuning, benchmark cherry-picking, or reported historical performance.
- **PREVIOUSLY INSPECTED:** any committed notebook/result/config that evaluates or plots 2025 returns/regimes for research decisions.

Copyright / changelog year strings do **not** count as empirical holdout inspection.

## Restrictions until FINAL CONFIGURATION FROZEN

1. Do **not** evaluate models on 2025 for final claims.
2. Development / validation work uses **2015–2023** (formation/dev) and **2024** (validation) only, once data is frozen.
3. Pre-registered experiment configs under `configs/experiments/` remain **`not-yet-frozen-for-holdout`** until development+validation complete and a tracker `FINAL CONFIGURATION FROZEN` record exists.

## Sign-off

| Field | Value |
|---|---|
| Holdout status | **CLEAR** |
| Prior empirical 2025 evaluation artifacts | **null** (none found) |
| Ready for acquisition + pre-registration | **yes** |
