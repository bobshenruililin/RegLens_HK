"""Ensure sibling lawtrace_worker is importable under RegLens PYTHONPATH."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_LT = _ROOT / "services" / "lawtrace-worker"
if str(_LT) not in sys.path:
    sys.path.insert(0, str(_LT))
