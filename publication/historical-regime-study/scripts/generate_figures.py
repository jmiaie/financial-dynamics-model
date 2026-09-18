#!/usr/bin/env python3
"""Deterministic figure generator for the D10-A publication pack.

Produces a bootstrap-CI forest plot from already-committed JSON artifacts
under `results/historical_regimes/`. No network calls, no randomness (all
values are read directly from committed bootstrap_records; nothing is
recomputed or re-sampled here).

If matplotlib is unavailable, this script exits cleanly with a message and
without writing any file -- callers should treat that as "skip figures",
not as a failure.

Usage:
    python publication/historical-regime-study/scripts/generate_figures.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:
    print("matplotlib not available -- skipping figure generation (see D10-STATUS.md).")
    sys.exit(0)


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def forest_plot_qqq_2025_h1(repo_root: Path, out_dir: Path) -> None:
    """Bootstrap-CI forest plot: QQQ 2025 holdout, horizon=1, FDM pipeline,
    all observed regimes, both bootstrap methods -- the exact figure backing
    CASE-STUDY.md and TECHNICAL-PAPER.md's bootstrap-uncertainty section.
    Source: results/historical_regimes/fdm_hist_regime_v1_robustness_qqq_holdout_2025.json
    -> models[model==financial_dynamics_pipeline].bootstrap_records
    (horizon == 1)."""
    path = repo_root / "results" / "historical_regimes" / "fdm_hist_regime_v1_robustness_qqq_holdout_2025.json"
    doc = load_json(path)
    fdm = doc["models"][0]
    assert fdm["model"] == "financial_dynamics_pipeline"

    records = [r for r in fdm["bootstrap_records"] if r["horizon"] == 1]
    regimes = sorted({r["regime"] for r in records})
    methods = ["moving_block", "stationary"]
    method_colors = {"moving_block": "#2166ac", "stationary": "#b2182b"}
    method_labels = {"moving_block": "Moving-block", "stationary": "Stationary"}

    fig, ax = plt.subplots(figsize=(7.5, 3.2), dpi=150)
    y_positions: dict[tuple[str, str], float] = {}
    y = 0.0
    yticks: list[float] = []
    yticklabels: list[str] = []
    offsets = {"moving_block": 0.18, "stationary": -0.18}
    for regime in regimes:
        for method in methods:
            rec = next(r for r in records if r["regime"] == regime and r["method"] == method)
            yy = y + offsets[method]
            y_positions[(regime, method)] = yy
            mean = rec["mean"]
            lo, hi = rec["ci_low"], rec["ci_high"]
            ax.plot([lo, hi], [yy, yy], color=method_colors[method], linewidth=1.6, zorder=2)
            ax.plot(mean, yy, "o", color=method_colors[method], markersize=5, zorder=3,
                     label=method_labels[method] if regime == regimes[0] else None)
        yticks.append(y)
        n = next(r for r in records if r["regime"] == regime)["n"]
        yticklabels.append(f"{regime}\n(n={n})")
        y += 1.0

    ax.axvline(0.0, color="#666666", linewidth=0.8, linestyle="--", zorder=1)
    ax.set_yticks(yticks)
    ax.set_yticklabels(yticklabels)
    ax.set_xlabel("1-day forward return (mean, 90% block-bootstrap CI)")
    ax.set_title(
        "QQQ 2025 holdout -- block-bootstrap CI on regime-conditional mean h1 return\n"
        "(cross-asset robustness / post-primary characterization -- NOT the SPY primary result)",
        fontsize=9,
    )
    ax.legend(loc="lower right", fontsize=8, frameon=False)
    ax.tick_params(axis="both", labelsize=8)
    fig.text(
        0.01, 0.01,
        "Source: results/historical_regimes/fdm_hist_regime_v1_robustness_qqq_holdout_2025.json "
        "(bootstrap_records; horizon=1); 1000 resamples, block length 20, seed=0.",
        fontsize=6, color="#555555",
    )
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    out_path = out_dir / "qqq_2025_holdout_bootstrap_ci_h1.png"
    fig.savefig(out_path)
    plt.close(fig)
    print(f"Wrote {out_path}")


def sparse_cell_histogram(repo_root: Path, out_dir: Path) -> None:
    """Histogram of effective block sizes actually reported across all
    bootstrap_records with n < 20, illustrating the sparse-cell disclosure
    (block_size = max(1, min(20, n))). Purely descriptive of already-committed
    numbers; no simulation."""
    results_dir = repo_root / "results" / "historical_regimes"
    symbols = ["spy", "qqq", "iwm", "tlt", "gld"]
    periods = ["dev_formation", "val_2024", "holdout_2025"]
    effective_blocks: list[int] = []
    for symbol in symbols:
        for period in periods:
            path = results_dir / f"fdm_hist_regime_v1_robustness_{symbol}_{period}.json"
            doc = load_json(path)
            for model in doc["models"]:
                for rec in model.get("bootstrap_records", []):
                    if rec["n"] < 20:
                        effective_blocks.append(rec["block_size"])

    fig, ax = plt.subplots(figsize=(6.0, 3.0), dpi=150)
    max_block = max(effective_blocks) if effective_blocks else 20
    bins = range(1, max_block + 2)
    ax.hist(effective_blocks, bins=bins, color="#4393c3", edgecolor="white", align="left")
    ax.set_xlabel("Effective block size actually reported (block_size field)")
    ax.set_ylabel("Count of bootstrap_records rows")
    ax.set_title(
        f"Sparse-cell effective block-size reduction\n"
        f"({len(effective_blocks)} rows with n < requested block length 20)",
        fontsize=9,
    )
    ax.tick_params(axis="both", labelsize=8)
    fig.text(
        0.01, 0.01,
        "Source: all 15 results/historical_regimes/*_robustness_*.json artifacts;\n"
        "effective_block = max(1, min(20, n)), metrics.py:block_bootstrap_mean_ci.",
        fontsize=6, color="#555555",
    )
    fig.tight_layout(rect=(0, 0.12, 1, 1))
    out_path = out_dir / "sparse_cell_effective_block_sizes.png"
    fig.savefig(out_path)
    plt.close(fig)
    print(f"Wrote {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[3],
    )
    args = parser.parse_args()
    repo_root: Path = args.repo_root.resolve()
    out_dir = repo_root / "publication" / "historical-regime-study" / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)

    forest_plot_qqq_2025_h1(repo_root, out_dir)
    sparse_cell_histogram(repo_root, out_dir)


if __name__ == "__main__":
    main()
