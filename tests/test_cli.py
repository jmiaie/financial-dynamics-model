"""Tests for the CLI entry point."""

from __future__ import annotations

import subprocess
import sys


class TestCLI:
    def test_version_flag(self):
        result = subprocess.run(
            [sys.executable, "-m", "financial_dynamics", "--version"],
            capture_output=True,
            text=True,
            env={"PYTHONPATH": "src"},
        )
        assert result.returncode == 0
        assert "financial-dynamics" in result.stdout
        assert "1.1.0" in result.stdout

    def test_help_flag(self):
        result = subprocess.run(
            [sys.executable, "-m", "financial_dynamics", "--help"],
            capture_output=True,
            text=True,
            env={"PYTHONPATH": "src"},
        )
        assert result.returncode == 0
        assert "Bayesian regime classification" in result.stdout
        assert "--period" in result.stdout
        assert "--forecast" in result.stdout
