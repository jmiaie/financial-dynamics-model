"""Chronology-safe historical regime study on frozen local datasets.

Uses only local CSVs under data/raw/ (gitignored). Never downloads in CI.
Holdout (2025) evaluation must be explicitly enabled after config freeze.
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from financial_dynamics.backtesting.metrics import (
    historical_regime_statistics,
    regime_bootstrap_uncertainty,
)
from financial_dynamics.benchmarks.baselines import (
    BaselineClassifier,
    GaussianMixtureClassifier,
    PersistenceClassifier,
    TrendVolGridClassifier,
    VolatilityBucketClassifier,
)
from financial_dynamics.config import PipelineConfig
from financial_dynamics.pipeline import FinancialDynamicsPipeline

OHLCV = ["open", "high", "low", "close", "volume"]


def _records(df: pd.DataFrame) -> list[dict[str, Any]]:
    """DataFrame.to_dict(orient="records") typed as list[dict[Hashable, Any]];
    columns here are always strings, so coerce keys to match ModelPeriodResult's contract."""
    return [{str(k): v for k, v in record.items()} for record in df.to_dict(orient="records")]


@dataclass(frozen=True)
class PeriodSpec:
    name: str
    start: str
    end_inclusive: str


@dataclass
class ModelPeriodResult:
    model: str
    evaluated_bars: int
    regime_counts: dict[str, int]
    summary_records: list[dict[str, Any]]
    transition_records: list[dict[str, Any]]
    key_metrics: dict[str, Any]
    # Populated only when run_historical_period(include_bootstrap=True):
    # block-bootstrap CIs on mean forward_return per (regime, horizon, method).
    # Empty by default so existing DEV/VAL/holdout re-runs are unaffected.
    bootstrap_records: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class StudyArtifacts:
    experiment_id: str
    dataset_id: str
    config_path: str
    primary_symbol: str
    period: PeriodSpec
    history_period: PeriodSpec | None
    seed: int
    horizons: list[int]
    pipeline_config_snapshot: dict[str, Any]
    models: list[ModelPeriodResult] = field(default_factory=list)
    created_utc: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        if self.history_period is None:
            payload["history_period"] = None
        return payload


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_frozen_symbol_csv(path: Path) -> pd.DataFrame:
    """Load one frozen Yahoo CSV and normalize to lowercase OHLCV."""
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    if df.index.has_duplicates:
        raise ValueError(f"Duplicate timestamps in {path}")
    rename = {c: c.lower().replace(" ", "_") for c in df.columns}
    df = df.rename(columns=rename)
    missing = [c for c in OHLCV if c not in df.columns]
    if missing:
        raise ValueError(f"{path} missing OHLCV columns {missing}; have {list(df.columns)}")
    keep = OHLCV + [c for c in df.columns if c not in OHLCV]
    return df.loc[:, keep]


def build_multi_asset_frame(
    raw_dir: Path,
    *,
    primary: str = "SPY",
    references: list[str] | None = None,
) -> pd.DataFrame:
    """Build primary OHLCV + ref_{SYM}_close columns from frozen CSVs."""
    references = references or ["QQQ", "IWM", "TLT", "GLD"]
    primary_df = load_frozen_symbol_csv(raw_dir / f"{primary}.csv")
    out = primary_df[OHLCV].copy()
    for symbol in references:
        if symbol == primary:
            continue
        ref = load_frozen_symbol_csv(raw_dir / f"{symbol}.csv")
        out[f"ref_{symbol}_close"] = ref["close"].reindex(out.index)
    # Drop rows missing primary OHLCV; keep ref NaNs only if any (should be rare for ETFs)
    if out[OHLCV].isna().any().any():
        raise ValueError("Primary OHLCV contains missing values after load")
    return out


def slice_period(df: pd.DataFrame, period: PeriodSpec) -> pd.DataFrame:
    start = pd.Timestamp(period.start)
    end = pd.Timestamp(period.end_inclusive) + pd.Timedelta(days=1)
    sliced = df.loc[(df.index >= start) & (df.index < end)].copy()
    if sliced.empty:
        raise ValueError(
            f"Empty slice for period {period.name} [{period.start}, {period.end_inclusive}]"
        )
    return sliced


def pipeline_config_from_experiment_yaml(path: Path) -> tuple[dict[str, Any], PipelineConfig]:
    """Load experiment YAML and map model feature/regime knobs into PipelineConfig."""
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Experiment config must be a mapping: {path}")

    config = PipelineConfig()
    model = raw.get("model") or {}
    features = model.get("features") or {}
    for key in (
        "volatility_span",
        "trend_window",
        "drawdown_window",
        "correlation_window",
        "shock_threshold",
        "normalization_method",
        "normalization_window",
    ):
        if key in features:
            setattr(config.features, key, features[key])

    # Optional explicit pipeline overrides under model.pipeline_overrides
    overrides = model.get("pipeline_overrides") or {}
    section_map = {
        "features": config.features,
        "regimes": config.regimes,
        "transitions": config.transitions,
        "stabilization": config.stabilization,
        "risk": config.risk,
    }
    for section, values in overrides.items():
        if section not in section_map or not isinstance(values, dict):
            continue
        target = section_map[section]
        for key, value in values.items():
            if hasattr(target, key):
                setattr(target, key, value)

    return raw, config


def snapshot_pipeline_config(config: PipelineConfig) -> dict[str, Any]:
    return {
        "features": vars(deepcopy(config.features)),
        "regimes": {
            "temperature": config.regimes.temperature,
            "centroids": deepcopy(config.regimes.centroids),
        },
        "transitions": vars(deepcopy(config.transitions)),
        "stabilization": vars(deepcopy(config.stabilization)),
        "risk": vars(deepcopy(config.risk)),
    }


def infer_regimes_with_history(
    history_df: pd.DataFrame,
    eval_df: pd.DataFrame,
    config: PipelineConfig,
) -> pd.Series:
    """Run FDM with optional history warmup; return eval-window regimes."""
    pipeline = FinancialDynamicsPipeline(deepcopy(config))
    if history_df.empty:
        results = pipeline.run(eval_df)
        return results["risk_adjusted_regime"]
    combined = pd.concat([history_df, eval_df], axis=0)
    results = pipeline.run(combined)
    return results.iloc[len(history_df) :]["risk_adjusted_regime"]


def _summarize_key_metrics(summary: pd.DataFrame, transitions: pd.DataFrame) -> dict[str, Any]:
    if summary.empty:
        return {
            "n_regimes_observed": 0,
            "mean_return_h1": None,
            "mean_return_h5": None,
            "mean_return_h20": None,
            "mean_realized_vol_h1": None,
            "mean_self_transition": None,
        }
    out: dict[str, Any] = {
        "n_regimes_observed": int(summary["regime"].nunique()),
        "mean_self_transition": (
            float(summary.drop_duplicates("regime")["transition_rate"].mean())
            if "transition_rate" in summary.columns
            else None
        ),
    }
    for horizon in (1, 5, 20):
        sub = summary[summary["horizon"] == horizon]
        out[f"mean_return_h{horizon}"] = float(sub["mean_return"].mean()) if not sub.empty else None
        out[f"mean_realized_vol_h{horizon}"] = (
            float(sub["realized_vol"].mean()) if not sub.empty else None
        )
        out[f"median_return_h{horizon}"] = (
            float(sub["median_return"].mean()) if not sub.empty else None
        )
        # Cross-regime averages of the per-occurrence robustness metrics
        # (see financial_dynamics.backtesting.metrics.historical_regime_statistics):
        # downside vol, positive-return frequency, 5th-percentile tail return,
        # and adverse (intra-horizon peak-to-trough) drawdown -- both the
        # cross-regime mean and the single worst regime-level figure, since
        # averaging away the worst regime would hide exactly the tail risk
        # this metric exists to surface.
        out[f"mean_downside_vol_h{horizon}"] = (
            float(sub["downside_vol"].mean()) if not sub.empty else None
        )
        out[f"mean_positive_return_freq_h{horizon}"] = (
            float(sub["positive_return_freq"].mean()) if not sub.empty else None
        )
        out[f"mean_tail_q05_h{horizon}"] = float(sub["tail_q05"].mean()) if not sub.empty else None
        out[f"mean_adverse_drawdown_h{horizon}"] = (
            float(sub["mean_adverse_drawdown"].mean())
            if not sub.empty and "mean_adverse_drawdown" in sub.columns
            else None
        )
        out[f"worst_adverse_drawdown_h{horizon}"] = (
            float(sub["worst_adverse_drawdown"].min())
            if not sub.empty and "worst_adverse_drawdown" in sub.columns
            else None
        )
    out["mean_duration_bars"] = (
        float(summary.drop_duplicates("regime")["mean_duration"].mean())
        if "mean_duration" in summary.columns
        else None
    )
    out["transition_matrix_shape"] = list(transitions.shape)
    return out


def _characterize(
    eval_df: pd.DataFrame,
    regimes: pd.Series,
    horizons: tuple[int, ...],
    *,
    include_bootstrap: bool = False,
    bootstrap_block_size: int = 20,
    bootstrap_n_resamples: int = 1000,
    bootstrap_seed: int = 0,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any], dict[str, int], list[dict[str, Any]]]:
    aligned = regimes.reindex(eval_df.index)
    stats = historical_regime_statistics(eval_df["close"], aligned, horizons=horizons)
    counts = {str(k): int(v) for k, v in aligned.dropna().value_counts().sort_index().items()}
    key = _summarize_key_metrics(stats.summary, stats.transitions)
    key["evaluated_bars"] = int(aligned.notna().sum())
    key["total_bars"] = len(eval_df)
    bootstrap_records: list[dict[str, Any]] = []
    if include_bootstrap:
        bootstrap_table = regime_bootstrap_uncertainty(
            stats.forward_occurrences,
            block_size=bootstrap_block_size,
            n_bootstrap=bootstrap_n_resamples,
            seed=bootstrap_seed,
        )
        bootstrap_records = _records(bootstrap_table)
    return stats.summary, stats.transitions, key, counts, bootstrap_records


def _default_baselines(seed: int) -> list[BaselineClassifier]:
    return [
        PersistenceClassifier(),
        VolatilityBucketClassifier(),
        TrendVolGridClassifier(),
        GaussianMixtureClassifier(random_state=seed),
    ]


def run_historical_period(
    *,
    experiment_id: str,
    dataset_id: str,
    config_path: str,
    panel: pd.DataFrame,
    eval_period: PeriodSpec,
    history_period: PeriodSpec | None,
    pipeline_config: PipelineConfig,
    horizons: tuple[int, ...] = (1, 5, 20),
    seed: int = 0,
    primary_symbol: str = "SPY",
    include_benchmarks: bool = True,
    include_bootstrap: bool = False,
    bootstrap_block_size: int = 20,
    bootstrap_n_resamples: int = 1000,
    notes: str = "",
) -> StudyArtifacts:
    """Run FDM (+ optional baselines) on one calendar period using frozen data.

    include_bootstrap adds moving-block and stationary block-bootstrap CIs
    (see financial_dynamics.backtesting.metrics.regime_bootstrap_uncertainty)
    to each model's bootstrap_records. Off by default -- it does not change
    any already-committed artifact unless explicitly requested, and is
    compute-heavier than the rest of this function."""
    eval_df = slice_period(panel, eval_period)
    history_df = (
        slice_period(panel, history_period) if history_period is not None else eval_df.iloc[0:0]
    )

    artifacts = StudyArtifacts(
        experiment_id=experiment_id,
        dataset_id=dataset_id,
        config_path=config_path,
        primary_symbol=primary_symbol,
        period=eval_period,
        history_period=history_period,
        seed=seed,
        horizons=list(horizons),
        pipeline_config_snapshot=snapshot_pipeline_config(pipeline_config),
        created_utc=_utc_now(),
        notes=notes,
    )

    fdm_regimes = infer_regimes_with_history(history_df, eval_df, pipeline_config)
    summary, transitions, key, counts, bootstrap_records = _characterize(
        eval_df,
        fdm_regimes,
        horizons,
        include_bootstrap=include_bootstrap,
        bootstrap_block_size=bootstrap_block_size,
        bootstrap_n_resamples=bootstrap_n_resamples,
        bootstrap_seed=seed,
    )
    artifacts.models.append(
        ModelPeriodResult(
            model="financial_dynamics_pipeline",
            evaluated_bars=int(fdm_regimes.notna().sum()),
            regime_counts=counts,
            summary_records=_records(summary),
            transition_records=_records(
                transitions.reset_index().rename(columns={"from_regime": "from_regime"})
            ),
            key_metrics=key,
            bootstrap_records=bootstrap_records,
        )
    )

    if not include_benchmarks:
        return artifacts

    # Persistence uses FDM-inferred history regimes as the observed last label source.
    history_fdm = (
        infer_regimes_with_history(history_df.iloc[0:0], history_df, pipeline_config)
        if len(history_df) > 0
        else pd.Series(dtype=object)
    )

    for baseline in _default_baselines(seed):
        if isinstance(baseline, PersistenceClassifier):
            if history_fdm.dropna().empty:
                # No history: cannot fit persistence honestly.
                continue
            preds = baseline.fit(history_df, history_fdm).predict(eval_df, history_df=history_df)
        else:
            if history_df.empty:
                preds = baseline.fit(eval_df).predict(eval_df)
            else:
                preds = baseline.fit(history_df).predict(eval_df, history_df=history_df)
        summary_b, transitions_b, key_b, counts_b, bootstrap_records_b = _characterize(
            eval_df,
            preds,
            horizons,
            include_bootstrap=include_bootstrap,
            bootstrap_block_size=bootstrap_block_size,
            bootstrap_n_resamples=bootstrap_n_resamples,
            bootstrap_seed=seed,
        )
        artifacts.models.append(
            ModelPeriodResult(
                model=baseline.name,
                evaluated_bars=int(preds.notna().sum()),
                regime_counts=counts_b,
                summary_records=_records(summary_b),
                transition_records=_records(transitions_b.reset_index()),
                key_metrics=key_b,
                bootstrap_records=bootstrap_records_b,
            )
        )

    return artifacts


def write_artifacts(artifacts: StudyArtifacts, out_dir: Path) -> tuple[Path, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{artifacts.experiment_id}.json"
    path.write_text(
        json.dumps(artifacts.to_dict(), indent=2, sort_keys=False) + "\n", encoding="utf-8"
    )
    return path, sha256_file(path)
