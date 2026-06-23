"""Save and load full pipeline state to/from JSON files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from financial_dynamics.config import PipelineConfig
from financial_dynamics.pipeline import FinancialDynamicsPipeline
from financial_dynamics.types import Regime


def save_state(pipeline: FinancialDynamicsPipeline, path: str | Path) -> None:
    """Serialize the full pipeline state to a JSON file.

    Captures all learned parameters and internal buffers so the pipeline
    can resume processing from exactly where it left off.
    """
    state = _extract_state(pipeline)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(state, f, indent=2)


def load_state(path: str | Path) -> FinancialDynamicsPipeline:
    """Deserialize a pipeline from a saved JSON state file.

    Returns a fully restored FinancialDynamicsPipeline that can continue
    processing new bars as if it had never stopped.
    """
    path = Path(path)
    with open(path) as f:
        state = json.load(f)

    config = PipelineConfig()
    _restore_config(config, state.get("config", {}))

    pipeline = FinancialDynamicsPipeline(config)
    _restore_state(pipeline, state)
    return pipeline


def _extract_state(pipeline: FinancialDynamicsPipeline) -> dict[str, Any]:
    """Extract all mutable state from the pipeline into a serializable dict."""
    fe = pipeline._feature_engine
    te = pipeline._transition_engine
    se = pipeline._stabilization_engine
    re = pipeline._risk_engine

    return {
        "version": 1,
        "bar_count": pipeline._bar_count,
        "config": pipeline.config.to_dict(),
        "feature_engine": {
            "close_buffer": list(fe._close_buffer),
            "normalizer_history": [arr.tolist() for arr in fe.normalizer._history],
        },
        "transition_engine": {
            "counts": te.counts.tolist(),
            "transition_matrix": te._transition_matrix.tolist(),
            "prev_regime": _regime_value(te._prev_regime),
        },
        "stabilization_engine": {
            "current_regime": se._current_regime.value,
            "persistence": {
                "confirmed_regime": _regime_value(se._persistence._confirmed_regime),
                "candidate": _regime_value(se._persistence._candidate),
                "candidate_count": se._persistence._candidate_count,
            },
            "majority_vote_buffer": [r.value for r in se._majority._buffer],
        },
        "risk_engine": {
            "overextension_history": [r.value for r in re._overextension._history],
            "chop_history": [r.value for r in re._chop_suppressor._history],
        },
    }


def _regime_value(regime: Regime | None) -> int | None:
    """Convert a nullable Regime to its int value, or return None."""
    return regime.value if regime is not None else None


def _optional_regime(value: int | None) -> Regime | None:
    """Convert a nullable int to a Regime, or return None."""
    return Regime(value) if value is not None else None


def _restore_state(pipeline: FinancialDynamicsPipeline, state: dict[str, Any]) -> None:
    """Restore mutable state into an existing pipeline instance."""
    pipeline._bar_count = state["bar_count"]

    fe = pipeline._feature_engine
    fe_state = state["feature_engine"]
    fe._close_buffer.clear()
    fe._close_buffer.extend(fe_state["close_buffer"])
    fe.normalizer._history = [np.array(arr) for arr in fe_state["normalizer_history"]]

    te = pipeline._transition_engine
    te_state = state["transition_engine"]
    te.counts = np.array(te_state["counts"])
    te._transition_matrix = np.array(te_state["transition_matrix"])
    te._prev_regime = _optional_regime(te_state["prev_regime"])

    se = pipeline._stabilization_engine
    se_state = state["stabilization_engine"]
    se._current_regime = Regime(se_state["current_regime"])

    p_state = se_state["persistence"]
    se._persistence._confirmed_regime = _optional_regime(p_state["confirmed_regime"])
    se._persistence._candidate = _optional_regime(p_state["candidate"])
    se._persistence._candidate_count = p_state["candidate_count"]

    se._majority._buffer.clear()
    se._majority._buffer.extend(Regime(r) for r in se_state["majority_vote_buffer"])

    re = pipeline._risk_engine
    re_state = state["risk_engine"]
    re._overextension._history = [Regime(r) for r in re_state["overextension_history"]]
    re._chop_suppressor._history.clear()
    re._chop_suppressor._history.extend(Regime(r) for r in re_state["chop_history"])


def _restore_config(config: PipelineConfig, data: dict[str, Any]) -> None:
    """Apply saved config values onto an existing PipelineConfig."""
    section_map = {
        "features": config.features,
        "regimes": config.regimes,
        "transitions": config.transitions,
        "stabilization": config.stabilization,
        "risk": config.risk,
    }
    for section_name, section_obj in section_map.items():
        if section_name in data:
            for key, value in data[section_name].items():
                if hasattr(section_obj, key):
                    setattr(section_obj, key, value)
