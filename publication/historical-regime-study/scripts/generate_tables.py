#!/usr/bin/env python3
"""Deterministic, offline table generator for the historical regime study reproducibility bundle.

Reads ONLY already-committed JSON artifacts under `results/historical_regimes/`
and hashes them; writes Markdown/CSV tables under `publication/historical-regime-study/tables/`
and a machine-readable `source_map.json` used to build RESULT-SOURCE-MAP.md.

No network calls. No modification of any file under results/, configs/, src/, or data/.
Safe to re-run any number of times; output is a pure function of the committed artifacts.

Usage:
    python publication/historical-regime-study/scripts/generate_tables.py
(run from the repository root; also works from any cwd via --repo-root)
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

MODEL_LABELS = {
    "financial_dynamics_pipeline": "FDM pipeline",
    "persistence": "Persistence",
    "volatility_bucket": "Volatility-bucket",
    "trend_vol_grid": "Trend/vol grid",
    "gaussian_mixture": "Gaussian mixture",
}
MODEL_ORDER = [
    "financial_dynamics_pipeline",
    "persistence",
    "volatility_bucket",
    "trend_vol_grid",
    "gaussian_mixture",
]
PERIOD_LABELS = {
    "dev_formation": "Development / formation (2015-01-01 to 2023-12-31)",
    "val_2024": "Validation (2024-01-01 to 2024-12-31)",
    # Corrected 2026-09-18: "HISTORICAL EVALUATION" was a category error (see
    # SOURCE-GATE.md field 7 / its "Period classification detail" section).
    # Holdout status is established by research/holdout-audit.md's CLEAR
    # verdict plus freeze-then-single-execution, not by "2025 data existed
    # and was inspectable" (true of every holdout period, not evidence
    # either way).
    "holdout_2025": "Holdout (2025-01-01 to 2025-12-31) -- FINAL 2025 HOLDOUT EVALUATION (pre-study audit CLEAR; single execution under frozen config)",
}
PERIOD_ORDER = ["dev_formation", "val_2024", "holdout_2025"]
ROBUSTNESS_SYMBOLS = ["spy", "qqq", "iwm", "tlt", "gld"]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def fmt(x: float | int | None, digits: int = 6) -> str:
    if x is None:
        return "n/a"
    if isinstance(x, bool):
        return str(x)
    if isinstance(x, int):
        return str(x)
    return f"{x:.{digits}f}"


class SourceMap:
    """Accumulates (table_row_id -> {file, key_path, sha256, kind}) traceability rows.

    `kind` disambiguates what `sha256` actually means for this row:
      - "whole_file_sha256" (default): `sha256` IS the sha256 of the entire
        `file` -- directly re-verifiable with a plain `sha256sum`.
      - "field_value": `sha256` is the *value* of the JSON/YAML/text field
        named by `key_path` inside `file` (which, for the dataset_canonical
        fields, itself happens to look like a sha256 but is NOT the hash of
        `file` itself -- conflating the two was a real bug caught by
        verify_pack.py's `hashes` check when it initially assumed every row
        was a whole-file hash).
    """

    def __init__(self) -> None:
        self.rows: list[dict[str, str]] = []

    def add(
        self, row_id: str, file_rel: str, key_path: str, sha256: str, *, kind: str = "whole_file_sha256"
    ) -> None:
        self.rows.append(
            {"row_id": row_id, "file": file_rel, "key_path": key_path, "sha256": sha256, "kind": kind}
        )

    def write(self, out_path: Path) -> None:
        out_path.write_text(json.dumps(self.rows, indent=2) + "\n", encoding="utf-8")

    def write_markdown(self, out_path: Path) -> None:
        lines = [
            "### Full result -> source traceability table (machine-generated)",
            "",
            f"{len(self.rows)} rows. Regenerate with `python scripts/generate_tables.py` "
            "(writes this file and `source_map.json` together; never hand-edited).",
            "",
            "| Row ID | Source file | JSON key path | sha256 |",
            "|---|---|---|---|",
        ]
        for r in self.rows:
            lines.append(f"| `{r['row_id']}` | `{r['file']}` | `{r['key_path']}` | `{r['sha256']}` |")
        out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def relpath(repo_root: Path, path: Path) -> str:
    return str(path.relative_to(repo_root))


def gen_primary_tables(repo_root: Path, results_dir: Path, out_dir: Path, smap: SourceMap) -> dict[str, Any]:
    """Table set 1: SPY-v1 primary results, one table per period, all models
    present in that period's slim artifact. Source: fdm_hist_regime_v1_{period}.json
    -> models[i].key_metrics / regime_counts (the ONLY fields present in the
    intentionally-slim primary artifacts -- no bootstrap_records, no
    downside_vol/tail_q05/adverse_drawdown for these files; see report Sec 7)."""
    primary_data: dict[str, Any] = {}
    lines_all: list[str] = []
    for period in PERIOD_ORDER:
        path = results_dir / f"fdm_hist_regime_v1_{period}.json"
        doc = load_json(path)
        digest = sha256_file(path)
        rel = relpath(repo_root, path)
        primary_data[period] = {"path": rel, "sha256": digest, "doc": doc}

        header = (
            "| Model | Regimes | Bars | Self-trans. | mean ret h1 | mean ret h5 | "
            "mean ret h20 | median ret h1 | median ret h5 | median ret h20 | vol h5 | vol h20 |"
        )
        sep = "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"
        rows = [f"### SPY-v1 primary -- {PERIOD_LABELS[period]}", "", header, sep]
        for model in doc["models"]:
            mid = model["model"]
            km = model["key_metrics"]
            bars = f"{model['evaluated_bars']}/{km['total_bars']}"
            n_regimes = km["n_regimes_observed"]
            row = (
                f"| {MODEL_LABELS.get(mid, mid)} | {n_regimes} | {bars} | "
                f"{fmt(km['mean_self_transition'], 3)} | {fmt(km['mean_return_h1'])} | "
                f"{fmt(km['mean_return_h5'])} | {fmt(km['mean_return_h20'])} | "
                f"{fmt(km['median_return_h1'])} | {fmt(km['median_return_h5'])} | "
                f"{fmt(km['median_return_h20'])} | {fmt(km['mean_realized_vol_h5'], 5)} | "
                f"{fmt(km['mean_realized_vol_h20'], 5)} |"
            )
            rows.append(row)
            for hz_key, col in [
                ("mean_self_transition", "self_trans"),
                ("mean_return_h1", "mean_ret_h1"),
                ("mean_return_h5", "mean_ret_h5"),
                ("mean_return_h20", "mean_ret_h20"),
                ("median_return_h1", "median_ret_h1"),
                ("median_return_h5", "median_ret_h5"),
                ("median_return_h20", "median_ret_h20"),
                ("mean_realized_vol_h5", "vol_h5"),
                ("mean_realized_vol_h20", "vol_h20"),
            ]:
                smap.add(
                    f"primary.{period}.{mid}.{col}",
                    rel,
                    f"models[model=={mid}].key_metrics.{hz_key}",
                    digest,
                )
            smap.add(
                f"primary.{period}.{mid}.regime_counts",
                rel,
                f"models[model=={mid}].regime_counts",
                digest,
            )
        fdm = doc["models"][0]
        rc = fdm["regime_counts"]
        rows.append("")
        rows.append(
            "FDM regime counts: " + ", ".join(f"{k} {v}" for k, v in sorted(rc.items())) + "."
        )
        lines_all.extend(rows)
        lines_all.append("")

    out_path = out_dir / "primary_spy_v1.md"
    out_path.write_text("\n".join(lines_all) + "\n", encoding="utf-8")
    return primary_data


def gen_robustness_tables(
    repo_root: Path, results_dir: Path, out_dir: Path, smap: SourceMap
) -> dict[tuple[str, str], Any]:
    """Table set 2: cross-asset / SPY-v2 robustness -- FDM pipeline row per
    (symbol, period), pulled from the *_robustness_{symbol}_{period}.json
    artifacts' key_metrics + regime_counts (full, non-slim artifacts)."""
    robustness_data: dict[tuple[str, str], Any] = {}
    header = (
        "| Symbol | Period | Regimes | Bars | Self-trans. | ret h1 | ret h5 | ret h20 | "
        "downside vol h20 | pos-ret freq h20 | tail q05 h20 | adverse DD mean h20 | adverse DD worst h20 |"
    )
    sep = "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"
    lines = [
        "### Cross-asset robustness + SPY-v2 post-primary characterization "
        "(FDM pipeline, v2 dataset -- NOT primary)",
        "",
        header,
        sep,
    ]
    for symbol in ROBUSTNESS_SYMBOLS:
        for period in PERIOD_ORDER:
            path = results_dir / f"fdm_hist_regime_v1_robustness_{symbol}_{period}.json"
            doc = load_json(path)
            digest = sha256_file(path)
            rel = relpath(repo_root, path)
            robustness_data[(symbol, period)] = {"path": rel, "sha256": digest, "doc": doc}
            fdm = doc["models"][0]
            assert fdm["model"] == "financial_dynamics_pipeline"
            km = fdm["key_metrics"]
            bars = f"{fdm['evaluated_bars']}/{km['total_bars']}"
            row = (
                f"| {symbol.upper()} | {period} | {km['n_regimes_observed']} | {bars} | "
                f"{fmt(km['mean_self_transition'], 3)} | {fmt(km['mean_return_h1'])} | "
                f"{fmt(km['mean_return_h5'])} | {fmt(km['mean_return_h20'])} | "
                f"{fmt(km['mean_downside_vol_h20'], 5)} | {fmt(km['mean_positive_return_freq_h20'], 4)} | "
                f"{fmt(km['mean_tail_q05_h20'], 4)} | {fmt(km['mean_adverse_drawdown_h20'], 4)} | "
                f"{fmt(km['worst_adverse_drawdown_h20'], 4)} |"
            )
            lines.append(row)
            for hz_key, col in [
                ("mean_self_transition", "self_trans"),
                ("mean_return_h1", "ret_h1"),
                ("mean_return_h5", "ret_h5"),
                ("mean_return_h20", "ret_h20"),
                ("mean_downside_vol_h20", "downside_vol_h20"),
                ("mean_positive_return_freq_h20", "pos_ret_freq_h20"),
                ("mean_tail_q05_h20", "tail_q05_h20"),
                ("mean_adverse_drawdown_h20", "adverse_dd_mean_h20"),
                ("worst_adverse_drawdown_h20", "adverse_dd_worst_h20"),
            ]:
                smap.add(
                    f"robustness.{symbol}.{period}.{col}",
                    rel,
                    f"models[model==financial_dynamics_pipeline].key_metrics.{hz_key}",
                    digest,
                )
    out_path = out_dir / "robustness_cross_asset.md"
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return robustness_data


def gen_bootstrap_sparse_cell_table(
    repo_root: Path, results_dir: Path, out_dir: Path, smap: SourceMap
) -> list[dict[str, Any]]:
    """Table set 3: sparse-cell effective-block-size disclosure. Scans every
    bootstrap_records[] row across all 15 robustness/characterization
    artifacts and reports every row where n < the requested block length (20),
    i.e. every row where the reported block_size necessarily differs from the
    requested 20 by construction (effective_block = max(1, min(block_size, n)))."""
    sparse_rows: list[dict[str, Any]] = []
    for symbol in ROBUSTNESS_SYMBOLS:
        for period in PERIOD_ORDER:
            path = results_dir / f"fdm_hist_regime_v1_robustness_{symbol}_{period}.json"
            doc = load_json(path)
            digest = sha256_file(path)
            rel = relpath(repo_root, path)
            for model in doc["models"]:
                mid = model["model"]
                for i, rec in enumerate(model.get("bootstrap_records", [])):
                    if rec["n"] < 20:
                        sparse_rows.append(
                            {
                                "symbol": symbol.upper(),
                                "period": period,
                                "model": mid,
                                "regime": rec["regime"],
                                "horizon": rec["horizon"],
                                "method": rec["method"],
                                "n": rec["n"],
                                "requested_block_size": 20,
                                "effective_block_size": rec["block_size"],
                                "file": rel,
                                "sha256": digest,
                                "bootstrap_record_index": i,
                            }
                        )
    header = (
        "| Symbol | Period | Model | Regime | Horizon | Method | n | "
        "Requested block | Effective block (reported) |"
    )
    sep = "|---|---|---|---|---:|---|---:|---:|---:|"
    lines = [
        "### Sparse-cell effective block-size disclosure",
        "",
        f"Total bootstrap rows where n < 20 (requested block length): **{len(sparse_rows)}**",
        "",
        header,
        sep,
    ]
    for r in sparse_rows:
        lines.append(
            f"| {r['symbol']} | {r['period']} | {r['model']} | {r['regime']} | {r['horizon']} | "
            f"{r['method']} | {r['n']} | {r['requested_block_size']} | {r['effective_block_size']} |"
        )
    (out_dir / "bootstrap_sparse_cells_full.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    for idx, r in enumerate(sparse_rows):
        smap.add(
            f"sparse_cell.{idx}.{r['symbol']}.{r['period']}.{r['model']}.{r['regime']}.h{r['horizon']}.{r['method']}",
            r["file"],
            f"models[model=={r['model']}].bootstrap_records[{r['bootstrap_record_index']}].block_size",
            r["sha256"],
        )
    return sparse_rows


def gen_case_study_record(
    repo_root: Path, results_dir: Path, smap: SourceMap
) -> dict[str, Any]:
    """Extracts the exact QQQ 2025-holdout RISK_OFF h1 bootstrap record used
    in CASE-STUDY.md, from both current values and the field-level diff
    against the pre-fix (150-resample) superseded artifact."""
    path = results_dir / "fdm_hist_regime_v1_robustness_qqq_holdout_2025.json"
    doc = load_json(path)
    digest = sha256_file(path)
    rel = relpath(repo_root, path)
    fdm = doc["models"][0]
    assert fdm["model"] == "financial_dynamics_pipeline"

    summary_rec = next(
        r for r in fdm["summary_records"] if r["regime"] == "RISK_OFF" and r["horizon"] == 1
    )
    boot_mb = next(
        r
        for r in fdm["bootstrap_records"]
        if r["regime"] == "RISK_OFF" and r["horizon"] == 1 and r["method"] == "moving_block"
    )
    boot_st = next(
        r
        for r in fdm["bootstrap_records"]
        if r["regime"] == "RISK_OFF" and r["horizon"] == 1 and r["method"] == "stationary"
    )

    superseded_path = results_dir / "superseded_150_resamples" / "fdm_hist_regime_v1_robustness_qqq_holdout_2025.json"
    superseded_doc = load_json(superseded_path)
    superseded_digest = sha256_file(superseded_path)
    superseded_rel = relpath(repo_root, superseded_path)
    superseded_fdm = superseded_doc["models"][0]
    superseded_boot_mb = next(
        r
        for r in superseded_fdm["bootstrap_records"]
        if r["regime"] == "RISK_OFF" and r["horizon"] == 1 and r["method"] == "moving_block"
    )

    smap.add(
        "case_study.qqq_2025.regime_counts",
        rel,
        "models[model==financial_dynamics_pipeline].regime_counts.RISK_OFF",
        digest,
    )
    smap.add(
        "case_study.qqq_2025.summary_record",
        rel,
        "models[model==financial_dynamics_pipeline].summary_records["
        "regime==RISK_OFF,horizon==1]",
        digest,
    )
    smap.add(
        "case_study.qqq_2025.bootstrap_moving_block",
        rel,
        "models[model==financial_dynamics_pipeline].bootstrap_records["
        "regime==RISK_OFF,horizon==1,method==moving_block]",
        digest,
    )
    smap.add(
        "case_study.qqq_2025.bootstrap_stationary",
        rel,
        "models[model==financial_dynamics_pipeline].bootstrap_records["
        "regime==RISK_OFF,horizon==1,method==stationary]",
        digest,
    )
    smap.add(
        "case_study.qqq_2025.superseded_150_resample_moving_block",
        superseded_rel,
        "models[model==financial_dynamics_pipeline].bootstrap_records["
        "regime==RISK_OFF,horizon==1,method==moving_block]",
        superseded_digest,
    )

    # TECHNICAL-PAPER.md Sec 4.2 and the forest-plot figure also quote
    # VOLATILE_TREND's (and CHOP's) horizon-1 bootstrap records for contrast
    # against RISK_OFF -- map every horizon-1 regime/method combination in
    # this file, not just RISK_OFF, so none of the figure's/paper's numbers
    # is an orphaned citation (found during independent review).
    other_regime_records: dict[str, dict[str, Any]] = {}
    for rec in fdm["bootstrap_records"]:
        if rec["horizon"] != 1 or rec["regime"] == "RISK_OFF":
            continue
        key = f"{rec['regime']}.{rec['method']}"
        other_regime_records[key] = rec
        smap.add(
            f"case_study.qqq_2025.bootstrap_{rec['regime'].lower()}_{rec['method']}",
            rel,
            f"models[model==financial_dynamics_pipeline].bootstrap_records["
            f"regime=={rec['regime']},horizon==1,method=={rec['method']}]",
            digest,
        )

    return {
        "artifact_path": rel,
        "artifact_sha256": digest,
        "dataset_id": doc["dataset_id"],
        "config_path": doc["config_path"],
        "created_utc": doc["created_utc"],
        "regime_counts": fdm["regime_counts"],
        "evaluated_bars": fdm["evaluated_bars"],
        "summary_record": summary_rec,
        "bootstrap_moving_block": boot_mb,
        "bootstrap_stationary": boot_st,
        "superseded_path": superseded_rel,
        "superseded_sha256": superseded_digest,
        "superseded_bootstrap_moving_block": superseded_boot_mb,
        "other_regimes_h1_bootstrap": other_regime_records,
    }


def gen_dataset_config_hash_table(
    repo_root: Path, out_dir: Path, smap: SourceMap
) -> dict[str, Any]:
    """Table set 4: dataset manifest / config hashes referenced throughout
    the pack (v1 primary + v2 robustness)."""
    targets = [
        ("dataset_v1_manifest", "data/manifests/yf_fd_etfs_daily_2015_2025_v1.json"),
        ("dataset_v2_manifest", "data/manifests/yf_fd_etfs_daily_2015_2025_v2.json"),
        ("dataset_v2_provenance", "data/manifests/yf_fd_etfs_daily_2015_2025_v2_PROVENANCE.md"),
        ("config_v1_primary", "configs/experiments/fdm_historical_regime_study_v1.yaml"),
        ("config_v2_robustness", "configs/experiments/fdm_historical_regime_study_v2_robustness.yaml"),
        ("holdout_audit", "research/holdout-audit.md"),
    ]
    result: dict[str, Any] = {}
    lines = ["### Dataset / config file hashes", "", "| Item | Path | sha256 (file) |", "|---|---|---|"]
    for key, rel in targets:
        path = repo_root / rel
        digest = sha256_file(path)
        result[key] = {"path": rel, "sha256": digest}
        lines.append(f"| {key} | `{rel}` | `{digest}` |")
        smap.add(f"hash_table.{key}", rel, "(whole file sha256)", digest)

    v1_manifest = load_json(repo_root / "data/manifests/yf_fd_etfs_daily_2015_2025_v1.json")
    v2_manifest = load_json(repo_root / "data/manifests/yf_fd_etfs_daily_2015_2025_v2.json")
    result["dataset_v1_canonical_sha256"] = v1_manifest["sha256"]["dataset_canonical"]
    result["dataset_v2_canonical_sha256"] = v2_manifest["sha256"]["dataset_canonical"]
    lines.append("")
    lines.append(f"`dataset_canonical` (v1, primary): `{result['dataset_v1_canonical_sha256']}`")
    lines.append(f"`dataset_canonical` (v2, robustness, non-hash-matching for SPY/QQQ/IWM/TLT): `{result['dataset_v2_canonical_sha256']}`")
    smap.add(
        "hash_table.dataset_v1_canonical",
        "data/manifests/yf_fd_etfs_daily_2015_2025_v1.json",
        "sha256.dataset_canonical",
        result["dataset_v1_canonical_sha256"],
        kind="field_value",
    )
    smap.add(
        "hash_table.dataset_v2_canonical",
        "data/manifests/yf_fd_etfs_daily_2015_2025_v2.json",
        "sha256.dataset_canonical",
        result["dataset_v2_canonical_sha256"],
        kind="field_value",
    )

    # CLAIM-REGISTER.md C19 (period-labeling claim) cites the primary config's
    # own freeze timestamp field -- map it explicitly so that citation is not
    # an orphan relative to the rest of this source map (found in
    # independent review).
    import yaml

    config_v1_path = repo_root / "configs/experiments/fdm_historical_regime_study_v1.yaml"
    config_v1_digest = sha256_file(config_v1_path)
    config_v1_doc = yaml.safe_load(config_v1_path.read_text(encoding="utf-8"))
    result["freeze_record_frozen_for_holdout_utc"] = config_v1_doc["freeze_record"][
        "frozen_for_holdout_utc"
    ]
    result["config_status"] = config_v1_doc["status"]
    lines.append(
        f"`freeze_record.frozen_for_holdout_utc` (v1 config): "
        f"`{result['freeze_record_frozen_for_holdout_utc']}`"
    )
    lines.append(f"`status` (v1 config): `{result['config_status']}`")
    smap.add(
        "hash_table.freeze_record_frozen_for_holdout_utc",
        "configs/experiments/fdm_historical_regime_study_v1.yaml",
        "freeze_record.frozen_for_holdout_utc",
        config_v1_digest,
    )
    smap.add(
        "hash_table.config_v1_status",
        "configs/experiments/fdm_historical_regime_study_v1.yaml",
        "status",
        config_v1_digest,
    )

    # CLAIM-REGISTER.md C19 (corrected 2026-09-18): holdout status rests on
    # research/holdout-audit.md's CLEAR verdict, not on "2025 data existed
    # and was inspectable" (a category error; see SOURCE-GATE.md field 7 /
    # its "Period classification detail" section).
    # Extract and map the verdict line itself so this citation is traceable
    # the same way every other one in this pack is.
    holdout_audit_path = repo_root / "research/holdout-audit.md"
    holdout_audit_digest = sha256_file(holdout_audit_path)
    holdout_audit_text = holdout_audit_path.read_text(encoding="utf-8")
    verdict_line = next(
        (line.strip() for line in holdout_audit_text.splitlines() if line.strip().startswith("**CLEAR**")),
        None,
    )
    result["holdout_audit_verdict"] = verdict_line
    lines.append(f"`research/holdout-audit.md` verdict line: {verdict_line}")
    smap.add(
        "hash_table.holdout_audit_verdict",
        "research/holdout-audit.md",
        "## Verdict (first CLEAR-prefixed line)",
        holdout_audit_digest,
    )

    (out_dir / "dataset_config_hashes.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[3],
        help="Repository root (default: inferred from this script's location).",
    )
    args = parser.parse_args()
    repo_root: Path = args.repo_root.resolve()
    results_dir = repo_root / "results" / "historical_regimes"
    out_dir = repo_root / "publication" / "historical-regime-study" / "tables"
    out_dir.mkdir(parents=True, exist_ok=True)

    smap = SourceMap()

    primary_data = gen_primary_tables(repo_root, results_dir, out_dir, smap)
    robustness_data = gen_robustness_tables(repo_root, results_dir, out_dir, smap)
    sparse_rows = gen_bootstrap_sparse_cell_table(repo_root, results_dir, out_dir, smap)
    case_study = gen_case_study_record(repo_root, results_dir, smap)
    hash_table = gen_dataset_config_hash_table(repo_root, out_dir, smap)

    smap.write(out_dir / "source_map.json")
    smap.write_markdown(out_dir / "source_map_full.md")

    manifest = {
        "generated_by": "publication/historical-regime-study/scripts/generate_tables.py",
        # Deliberately no absolute repo_root path here: this manifest is a
        # committed artifact that must be byte-identical when regenerated in
        # a different environment (e.g. a CI runner, whose checkout path is
        # necessarily different from a local clone's) -- an earlier version
        # of this script embedded str(repo_root) here, which broke exactly
        # that reproducibility guarantee the first time this pack's CI
        # workflow ran on a real GitHub Actions runner (verify_pack.py's
        # `tables` check correctly caught it: only this one field differed).
        "n_sparse_bootstrap_rows": len(sparse_rows),
        "primary_periods": list(primary_data.keys()),
        "robustness_symbols_periods": [f"{s}/{p}" for (s, p) in robustness_data],
        "case_study_summary": {
            "artifact_path": case_study["artifact_path"],
            "artifact_sha256": case_study["artifact_sha256"],
            "risk_off_n": case_study["regime_counts"].get("RISK_OFF"),
            "risk_off_mean_h1": case_study["summary_record"]["mean_return"],
            "risk_off_ci_low_moving_block": case_study["bootstrap_moving_block"]["ci_low"],
            "risk_off_ci_high_moving_block": case_study["bootstrap_moving_block"]["ci_high"],
        },
        "dataset_config_hashes": hash_table,
    }
    (out_dir / "generation_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    (out_dir / "case_study_record.json").write_text(
        json.dumps(case_study, indent=2) + "\n", encoding="utf-8"
    )

    print(f"Wrote tables to {out_dir}")
    print(f"  sparse bootstrap rows (n<20): {len(sparse_rows)}")
    print(f"  source_map rows: {len(smap.rows)}")


if __name__ == "__main__":
    main()
