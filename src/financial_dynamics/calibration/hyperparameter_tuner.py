"""Hyperparameter tuning via grid search using backtest accuracy as objective."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from itertools import product

import pandas as pd

from financial_dynamics.backtesting.evaluator import BacktestEvaluator
from financial_dynamics.config import PipelineConfig


@dataclass
class TuningResult:
    """Outcome of a hyperparameter search."""
    best_config: PipelineConfig
    best_accuracy: float
    best_params: dict[str, float | int]
    all_trials: pd.DataFrame


SearchSpace = dict[str, list[float | int]]


_DEFAULT_SPACE: SearchSpace = {
    "regimes.temperature": [0.5, 1.0, 1.5, 2.0],
    "transitions.learning_rate": [0.02, 0.05, 0.1],
    "stabilization.hysteresis_threshold": [0.1, 0.15, 0.25],
    "stabilization.min_persistence_bars": [3, 5, 8],
}


class HyperparameterTuner:
    """Grid search over a configurable hyperparameter space.

    Uses BacktestEvaluator's accuracy on labeled data as the objective.
    """

    def __init__(self, base_config: PipelineConfig | None = None) -> None:
        self.base_config = base_config or PipelineConfig()

    def tune(
        self,
        df: pd.DataFrame,
        labels: pd.Series,
        search_space: SearchSpace | None = None,
    ) -> TuningResult:
        """Run a grid search over the search space.

        Args:
            df: Training OHLCV data.
            labels: Ground-truth regime labels aligned with df.
            search_space: Dict mapping dotted config paths
                         (e.g. "regimes.temperature") to lists of values.
                         If None, uses a sensible default space.

        Returns:
            TuningResult with the best config and a DataFrame of all trials.
        """
        if search_space is None:
            space = _DEFAULT_SPACE
        else:
            if not search_space:
                raise ValueError("search_space must contain at least one parameter")
            space = search_space

        param_names = list(space.keys())
        value_grid = [space[name] for name in param_names]

        trials = []
        best_accuracy = -1.0
        best_config = self.base_config
        best_params: dict[str, float | int] = {}

        for values in product(*value_grid):
            params = dict(zip(param_names, values))
            trial_config = self._apply_params(self.base_config, params)
            evaluator = BacktestEvaluator(trial_config)
            result = evaluator.evaluate(df, labels)

            trials.append({**params, "accuracy": result.accuracy})

            if result.accuracy > best_accuracy:
                best_accuracy = result.accuracy
                best_config = trial_config
                best_params = params

        return TuningResult(
            best_config=best_config,
            best_accuracy=best_accuracy,
            best_params=best_params,
            all_trials=pd.DataFrame(trials),
        )

    @staticmethod
    def _apply_params(
        base_config: PipelineConfig,
        params: dict[str, float | int],
    ) -> PipelineConfig:
        """Return a deep-copied config with dotted-path overrides applied."""
        new_config = deepcopy(base_config)
        for path, value in params.items():
            section, key = path.split(".", 1)
            if not hasattr(new_config, section):
                raise ValueError(
                    f"Unknown config path '{path}' (no section '{section}')"
                )
            section_obj = getattr(new_config, section)
            if not hasattr(section_obj, key):
                raise ValueError(
                    f"Unknown config path '{path}' (section '{section}' has no '{key}')"
                )
            setattr(section_obj, key, value)
        return new_config
