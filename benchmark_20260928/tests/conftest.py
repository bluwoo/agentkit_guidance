import os
import sys

# Make the repo root (benchmark_20260928) importable so `harness` resolves.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
