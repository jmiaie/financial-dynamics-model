"""Re-exports safe_renormalize under the phase4_risk namespace.

The canonical implementation lives in financial_dynamics._utils;
this module exists so phase4_risk submodule consumers can import
from their own package without coupling to the top-level _utils path.
"""

from financial_dynamics._utils import safe_renormalize

__all__ = ["safe_renormalize"]
