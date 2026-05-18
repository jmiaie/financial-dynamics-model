"""Tests for Phase 1: Regime Probabilities."""

import numpy as np
import pytest

from financial_dynamics.config import RegimeConfig
from financial_dynamics.phase1_regimes.centroid_engine import CentroidEngine
from financial_dynamics.phase1_regimes.regime_definitions import (
    get_centroids,
    get_default_centroids,
)
from financial_dynamics.types import BarState, FeatureVector, Regime


class TestRegimeDefinitions:
    def test_default_centroids_shape(self):
        centroids = get_default_centroids()
        assert centroids.shape == (4, 5)

    def test_centroids_from_config(self):
        config = RegimeConfig()
        centroids = get_centroids(config)
        assert centroids.shape == (4, 5)
        np.testing.assert_array_equal(centroids, get_default_centroids())


class TestCentroidEngine:
    def test_probabilities_sum_to_one(self):
        engine = CentroidEngine()
        x = np.array([0.5, 0.5, 0.5, 0.5, 0.5])
        probs = engine.compute_probabilities(x)
        assert probs.probs.sum() == pytest.approx(1.0)

    def test_probabilities_nonnegative(self):
        engine = CentroidEngine()
        x = np.random.rand(5)
        probs = engine.compute_probabilities(x)
        assert (probs.probs >= 0).all()

    def test_exact_centroid_gives_dominant(self):
        engine = CentroidEngine()
        for regime in Regime:
            centroid = engine.centroids[int(regime)]
            probs = engine.compute_probabilities(centroid)
            assert probs.dominant == regime

    def test_near_centroid_high_confidence(self):
        engine = CentroidEngine()
        centroid = engine.centroids[int(Regime.CALM_TREND)]
        noisy = centroid + np.random.normal(0, 0.01, 5)
        probs = engine.compute_probabilities(noisy)
        assert probs.dominant == Regime.CALM_TREND
        assert probs.confidence > 0.3

    def test_temperature_effect(self):
        # Low temperature = more decisive (peakier)
        config_cold = RegimeConfig(temperature=0.3)
        config_hot = RegimeConfig(temperature=3.0)
        engine_cold = CentroidEngine(config_cold)
        engine_hot = CentroidEngine(config_hot)

        x = np.array([0.15, 0.75, 0.08, 0.12, 0.12])
        probs_cold = engine_cold.compute_probabilities(x)
        probs_hot = engine_hot.compute_probabilities(x)

        assert probs_cold.confidence > probs_hot.confidence

    def test_update_populates_bar_state(self):
        engine = CentroidEngine()
        state = BarState()
        state.features = FeatureVector(0.1, 0.8, 0.05, 0.1, 0.1)
        engine.update(state)
        assert state.raw_probabilities is not None
        assert state.raw_probabilities.probs.sum() == pytest.approx(1.0)

    def test_update_skips_if_no_features(self):
        engine = CentroidEngine()
        state = BarState()
        engine.update(state)
        assert state.raw_probabilities is None

    def test_set_centroids(self):
        engine = CentroidEngine()
        new_centroids = np.random.rand(4, 5)
        engine.set_centroids(new_centroids)
        np.testing.assert_array_equal(engine.centroids, new_centroids)
