# Contributing to Financial Dynamics Model

Thank you for your interest in contributing. This guide will help you get started.

## Development Setup

```bash
git clone https://github.com/jmiaie/financial-dynamics-model.git
cd financial-dynamics-model
pip install -e ".[all]"
pytest tests/ -v
```

## Making Changes

1. **Fork** the repo and create a branch from `main`
2. **Write code** — follow the existing style, no unnecessary abstractions
3. **Add tests** — all new features need test coverage
4. **Run tests** — `pytest tests/ -v` must pass (229+ tests)
5. **Open a PR** — use the PR template, explain what and why

## Code Style

- No comments unless the *why* is non-obvious
- No premature abstractions — three similar lines beats a helper nobody reads
- All probability vectors must sum to 1.0
- All transition matrix rows must sum to 1.0
- Validate at system boundaries only (user input, external APIs)

## Architecture

The pipeline has 5 phases, each independently testable:

| Phase | Module | Responsibility |
|-------|--------|----------------|
| 0 | `phase0_features/` | EWMA vol, trend, drawdown, corr stress, shock |
| 1 | `phase1_regimes/` | Softmax centroid classification |
| 2 | `phase2_transitions/` | Dirichlet-Bayesian Markov learning |
| 3 | `phase3_stabilization/` | Hysteresis, persistence, majority vote |
| 4 | `phase4_risk/` | Risk-Off confirmation, overextension |

Each phase reads from and writes to `BarState`. The `Pipeline` orchestrator calls each engine's `update()` method in sequence.

## Testing

```bash
pytest tests/ -v                          # All tests
pytest tests/test_phase0_features.py -v   # Specific module
pytest tests/test_stress.py -v            # Numerical stability
```

Key invariants checked in tests:
- Probability vectors sum to 1.0 (within tolerance)
- Transition matrix rows sum to 1.0
- All probabilities are non-negative
- Batch and streaming modes produce identical results

## Reporting Issues

Use the GitHub issue templates for bug reports and feature requests. Include a minimal reproducible example when possible.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
