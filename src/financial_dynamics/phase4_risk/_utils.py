"""Re-export of safe_renormalize so phase4_risk modules import from their own package."""

from __future__ import annotations

from financial_dynamics._utils import safe_renormalize

__all__ = ["safe_renormalize"]
