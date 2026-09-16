#!/usr/bin/env python3
"""Run Directive #9 historical regime study on frozen local data only.

Examples:
  # Development (2015-2023) + validation (2024); holdout blocked
  python scripts/run_historical_regime_study.py \\
    --config configs/experiments/fdm_historical_regime_study_v1.yaml

  # Holdout (2025) only after YAML status is frozen-for-holdout
  python scripts/run_historical_regime_study.py --allow-holdout
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from financial_dynamics.research.historical_study import (
    PeriodSpec,
    build_multi_asset_frame,
    pipeline_config_from_experiment_yaml,
    run_historical_period,
    write_artifacts,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _append_ledger(path: Path, row: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "experiment_id",
        "repo",
        "branch",
        "dataset_id",
        "config_path",
        "status",
        "period_name",
        "period_start",
        "period_end",
        "horizons",
        "seed",
        "primary_symbol",
        "artifact_path",
        "artifact_sha256",
        "key_metrics_json",
        "notes",
        "created_utc",
    ]
    exists = path.exists()
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if not exists:
            writer.writeheader()
        writer.writerow({k: row.get(k, "") for k in fieldnames})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/experiments/fdm_historical_regime_study_v1.yaml"),
    )
    parser.add_argument("--raw-dir", type=Path, default=None)
    parser.add_argument("--results-dir", type=Path, default=Path("results/historical_regimes"))
    parser.add_argument("--ledger", type=Path, default=Path("research/experiment-ledger.csv"))
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--branch", default="research/historical-regime-validation")
    parser.add_argument(
        "--allow-holdout",
        action="store_true",
        help="Run 2025 holdout only if experiment YAML status is frozen-for-holdout",
    )
    parser.add_argument(
        "--skip-dev",
        action="store_true",
        help="Skip formation/dev period run",
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip 2024 validation run",
    )
    args = parser.parse_args(argv)

    root = _repo_root()
    config_path = args.config if args.config.is_absolute() else root / args.config
    experiment, pipeline_config = pipeline_config_from_experiment_yaml(config_path)
    dataset_id = str(experiment["dataset_id"])
    status = str(experiment.get("status", ""))
    symbols = list(
        experiment.get("universe", {}).get("symbols", ["SPY", "QQQ", "IWM", "TLT", "GLD"])
    )
    primary = symbols[0]
    references = [s for s in symbols[1:]]
    horizons = tuple(
        int(h)
        for h in experiment.get("evaluation", {}).get("forward_horizons_trading_days", [1, 5, 20])
    )
    periods = experiment["periods"]
    formation = PeriodSpec(
        "formation_dev",
        periods["formation_dev"]["start"],
        periods["formation_dev"]["end_inclusive"],
    )
    validation = PeriodSpec(
        "validation",
        periods["validation"]["start"],
        periods["validation"]["end_inclusive"],
    )
    holdout = PeriodSpec(
        "holdout",
        periods["holdout"]["start"],
        periods["holdout"]["end_inclusive"],
    )

    raw_dir = args.raw_dir or (root / "data" / "raw" / dataset_id)
    if not raw_dir.is_dir():
        print(f"ERROR: frozen raw dir missing: {raw_dir}", file=sys.stderr)
        print("Acquire locally with scripts/acquire_yf_fd_etfs_daily.py (not CI).", file=sys.stderr)
        return 2

    panel = build_multi_asset_frame(raw_dir, primary=primary, references=references)
    results_dir = args.results_dir if args.results_dir.is_absolute() else root / args.results_dir
    ledger_path = args.ledger if args.ledger.is_absolute() else root / args.ledger

    runs: list[tuple[str, PeriodSpec, PeriodSpec | None, str]] = []
    if not args.skip_dev:
        runs.append(
            (
                "fdm_hist_regime_v1_dev_formation",
                formation,
                None,
                "Development/in-sample characterization on formation window; no holdout.",
            )
        )
    if not args.skip_validation:
        runs.append(
            (
                "fdm_hist_regime_v1_val_2024",
                validation,
                formation,
                "Validation OOS characterization; benchmarks fit on formation only.",
            )
        )
    if args.allow_holdout:
        if status not in {"frozen-for-holdout", "FROZEN_FOR_HOLDOUT"}:
            print(
                f"ERROR: refuse holdout; experiment status is '{status}', need frozen-for-holdout",
                file=sys.stderr,
            )
            return 3
        runs.append(
            (
                "fdm_hist_regime_v1_holdout_2025",
                holdout,
                PeriodSpec(
                    "pre_holdout",
                    formation.start,
                    validation.end_inclusive,
                ),
                "FINAL holdout evaluation after FINAL CONFIGURATION FROZEN.",
            )
        )

    if not runs:
        print("No periods selected.", file=sys.stderr)
        return 1

    for experiment_id, eval_period, history_period, notes in runs:
        print(f"Running {experiment_id} on {eval_period.name}...")
        artifacts = run_historical_period(
            experiment_id=experiment_id,
            dataset_id=dataset_id,
            config_path=str(config_path.relative_to(root)),
            panel=panel,
            eval_period=eval_period,
            history_period=history_period,
            pipeline_config=pipeline_config,
            horizons=horizons,
            seed=args.seed,
            primary_symbol=primary,
            include_benchmarks=True,
            notes=notes,
        )
        artifact_path, artifact_sha = write_artifacts(artifacts, results_dir)
        fdm = next(m for m in artifacts.models if m.model == "financial_dynamics_pipeline")
        print(
            f"  FDM bars={fdm.evaluated_bars} regimes={fdm.regime_counts} "
            f"key={json.dumps(fdm.key_metrics, sort_keys=True)}"
        )
        for model in artifacts.models:
            if model.model == "financial_dynamics_pipeline":
                continue
            print(
                f"  {model.model}: bars={model.evaluated_bars} "
                f"n_regimes={model.key_metrics.get('n_regimes_observed')} "
                f"mean_return_h1={model.key_metrics.get('mean_return_h1')}"
            )
        _append_ledger(
            ledger_path,
            {
                "experiment_id": experiment_id,
                "repo": "financial-dynamics-model",
                "branch": args.branch,
                "dataset_id": dataset_id,
                "config_path": str(config_path.relative_to(root)),
                "status": status,
                "period_name": eval_period.name,
                "period_start": eval_period.start,
                "period_end": eval_period.end_inclusive,
                "horizons": "|".join(str(h) for h in horizons),
                "seed": str(args.seed),
                "primary_symbol": primary,
                "artifact_path": str(artifact_path.relative_to(root)),
                "artifact_sha256": artifact_sha,
                "key_metrics_json": json.dumps(fdm.key_metrics, sort_keys=True),
                "notes": notes,
                "created_utc": artifacts.created_utc,
            },
        )
        print(f"  wrote {artifact_path} sha256={artifact_sha}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
