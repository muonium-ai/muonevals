"""Project-wide test configuration."""

import os
import sys

# Add muonledger Python package to sys.path
_muonledger_src = os.path.join(
    os.path.dirname(__file__), "muonledger", "port", "python", "src"
)
if _muonledger_src not in sys.path:
    sys.path.insert(0, _muonledger_src)
