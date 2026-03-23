"""Ensure muonledger is importable at runtime.

Import this module before using muonledger:
    import muonevals._muonledger_path  # noqa: F401
"""

import os
import sys

_muonledger_src = os.path.join(
    os.path.dirname(__file__), os.pardir, "muonledger", "port", "python", "src"
)
_muonledger_src = os.path.normpath(_muonledger_src)
if _muonledger_src not in sys.path:
    sys.path.insert(0, _muonledger_src)
