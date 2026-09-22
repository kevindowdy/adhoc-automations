"""Ensures the project root (where the automation scripts live) is importable."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
