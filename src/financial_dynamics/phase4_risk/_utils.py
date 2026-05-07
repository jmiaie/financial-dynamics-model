"""Re-export of safe_renormalize into the phase4_risk namespace.

All three Phase 4 modules (risk_overlay, overextension, chop_suppression)
import safe_renormalize from here rather than from the top-level _utils,
keeping their imports local to the phase package. The implementation lives
in financial_dynamics._utils.
"""

from financial_dynamics._utils import safe_renormalize

__all__ = ["safe_renormalize"]
