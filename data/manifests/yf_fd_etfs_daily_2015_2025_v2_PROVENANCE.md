# PROVENANCE — yf_fd_etfs_daily_2015_2025_v2

**Why this file exists.** The frozen v1 raw payload is absent from this repo (`data/raw/` is gitignored;
`data/` carries the manifest only — verified 2026-09-17, 0 CSV/parquet files). The agent session that
produced the primary D9-A result cannot re-acquire it: its egress proxy returns an organization-policy
403 for Yahoo Finance / FRED / SEC EDGAR (recorded in the D9 tracker as a deliberate policy denial).
Acquisition is therefore a local/agent run on an unrestricted node, exactly as
`scripts/acquire_yf_fd_etfs_daily.py` states ("never invoke from CI").

**How it was made.** 2026-09-17, an agent node with unrestricted egress, the repo's own acquisition
script unmodified, yfinance 1.7.0, parameters identical to v1 (`--start 2015-01-01 --end 2026-01-01`,
`interval 1d`, `auto_adjust True`, `actions True`, `repair False`, `keepna True`). (An internal
network address recorded in an earlier draft of this file has been redacted — it identifies
infrastructure, not the acquisition itself, and has no bearing on the data or its provenance.)

**Divergence from v1 — the load-bearing fact.**

| file | v1 sha256 (frozen) | v2 sha256 | match |
|---|---|---|---|
| `SPY.csv` | `f7f2a7dfdcb1e01b…` | `e5d6adc6ae471de1…` | **no** |
| `QQQ.csv` | `00968114e8e83ac1…` | `83e545c7b67b2589…` | **no** |
| `IWM.csv` | `6d255067e675c185…` | `24d9f10c8ae71a8b…` | **no** |
| `TLT.csv` | `8fe002b66d8c5d4e…` | `7e54e1f21a927385…` | **no** |
| `GLD.csv` | `661e1e4670253b59…` | `661e1e4670253b59…` | YES |

| | v1 | v2 |
|---|---|---|
| `dataset_canonical` | `91caa6cde08358091125a6576ff3f2be5666791b06df67d462c2aad6f771ada9` | `94ea2886772afc7adcbf070bf1563a59295c1e7b1f837e157dfe5880c5b12582` |
| yfinance | 1.7.0 | 1.7.0 |
| freeze/retrieval | 2026-09-16T02:37:02Z | 2026-09-17T02:27:37Z |

Identical across both: symbol set, row counts (2766 per symbol), `actual_start` 2015-01-02,
`actual_end` 2025-12-31, `missing_ohlcv_cells` 0.

**Interpretation.** Four of five files differ; GLD alone matches. GLD pays no distributions, so its
series is reproducible raw closes; SPY/QQQ/IWM/TLT carry dividend adjustment, which is not
bit-reproducible across retrievals. **The magnitude of the divergence is not quantifiable** — that
requires the v1 payload, which does not exist. That absence, not the size of the delta, is the finding.

**Consequence (program dataset-provenance rule).** This payload MUST NOT be presented as v1, merged into
v1 artifacts, or used to recompute the consumed primary result.

**Owner decision (2026-09-17): the true v1 payload is confirmed gone** — no machine that ran the
primary SPY acquisition still holds `data/raw/`. This payload is therefore **adopted as v2**: the
delta is documented above (this file), the SPY v1 result stays the primary consumed historical
result unchanged, and every output computed from this v2 payload (QQQ/IWM/TLT/GLD only — SPY v1 is
not re-run) is labeled pre-specified robustness / post-primary characterization, never a substitute
for or restatement of the primary result.

**Reproduce.** `python scripts/acquire_yf_fd_etfs_daily.py --dataset-id yf_fd_etfs_daily_2015_2025_v2 --raw-dir <dir>`
then compare per-file sha256 above. Re-running may produce a *different* hash again for the dividend-paying
symbols — that is the reproducibility risk this table exists to make visible.

**Storage on this branch.** Unlike an earlier draft of this payload (which committed the raw CSVs
under `data/snapshots/`), the raw bytes here are kept **local and gitignored under `data/raw/`**,
matching v1's own convention: this repository is public, and redistribution rights for vendor
(Yahoo Finance) market data have not been separately checked. Only this manifest and this
provenance file are committed. Anyone needing to reproduce the study must re-run the acquisition
script themselves; the resulting hash divergence for the dividend-paying symbols is expected and
does not indicate a broken reproduction, per the table above.
