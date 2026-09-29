"""Pytest configuration — ensures project root is on sys.path."""
import sys
from pathlib import Path

# Project root = parent of tests/
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
