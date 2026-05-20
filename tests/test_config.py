"""Tests for configuration loading and validation."""

from __future__ import annotations

import warnings

import pytest
import yaml

from financial_dynamics.config import (
    FeatureConfig,
    PipelineConfig,
    RegimeConfig,
    RiskConfig,
    StabilizationConfig,
    TransitionConfig,
)


class TestPipelineConfigDefaults:
    def test_default_config_has_all_sections(self):
        config = PipelineConfig()
        assert isinstance(config.features, FeatureConfig)
        assert isinstance(config.regimes, RegimeConfig)
        assert isinstance(config.transitions, TransitionConfig)
        assert isinstance(config.stabilization, StabilizationConfig)
        assert isinstance(config.risk, RiskConfig)

    def test_default_feature_config_values(self):
        config = PipelineConfig()
        assert config.features.volatility_span == 20
        assert config.features.trend_window == 14
        assert config.features.normalization_method == "zscore"

    def test_default_regime_temperature(self):
        config = PipelineConfig()
        assert config.regimes.temperature == 1.0


class TestFromYaml:
    def test_loads_default_yaml(self):
        config = PipelineConfig.from_yaml("config/default.yaml")
        assert config.features.volatility_span == 20
        assert config.regimes.temperature == 1.0
        assert config.transitions.prior_strength == 10.0

    def test_file_not_found_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="Pipeline config not found"):
            PipelineConfig.from_yaml(tmp_path / "nonexistent.yaml")

    def test_invalid_yaml_raises(self, tmp_path):
        bad_yaml = tmp_path / "bad.yaml"
        bad_yaml.write_text("{{invalid: yaml: [")
        with pytest.raises(ValueError, match="Invalid YAML"):
            PipelineConfig.from_yaml(bad_yaml)

    def test_non_mapping_yaml_raises(self, tmp_path):
        list_yaml = tmp_path / "list.yaml"
        list_yaml.write_text("- item1\n- item2\n")
        with pytest.raises(ValueError, match="Expected YAML mapping"):
            PipelineConfig.from_yaml(list_yaml)

    def test_empty_yaml_returns_defaults(self, tmp_path):
        empty = tmp_path / "empty.yaml"
        empty.write_text("")
        config = PipelineConfig.from_yaml(empty)
        default = PipelineConfig()
        assert config.features.volatility_span == default.features.volatility_span

    def test_partial_override(self, tmp_path):
        partial = tmp_path / "partial.yaml"
        partial.write_text(yaml.dump({"features": {"volatility_span": 30}}))
        config = PipelineConfig.from_yaml(partial)
        assert config.features.volatility_span == 30
        assert config.features.trend_window == 14  # unchanged default

    def test_unknown_key_warns(self, tmp_path):
        unknown = tmp_path / "unknown.yaml"
        unknown.write_text(yaml.dump({"features": {"nonexistent_param": 42}}))
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            PipelineConfig.from_yaml(unknown)
            assert any("Unknown config key" in str(warning.message) for warning in w)

    def test_multiple_sections_override(self, tmp_path):
        multi = tmp_path / "multi.yaml"
        multi.write_text(yaml.dump({
            "features": {"volatility_span": 50},
            "transitions": {"learning_rate": 0.1},
            "risk": {"riskoff_confirmation_count": 5},
        }))
        config = PipelineConfig.from_yaml(multi)
        assert config.features.volatility_span == 50
        assert config.transitions.learning_rate == 0.1
        assert config.risk.riskoff_confirmation_count == 5
