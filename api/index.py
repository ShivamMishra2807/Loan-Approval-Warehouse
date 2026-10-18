"""Vercel Serverless Entrypoint for FastAPI Application.
This file maps requests into the FastAPI instance defined in `src/ln/api.py`.
"""

import sys
from pathlib import Path

# Ensure project root and src are on the Python path
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
SRC_DIR = PROJECT_ROOT / "src"

for path in [str(SRC_DIR), str(PROJECT_ROOT)]:
    if path not in sys.path:
        sys.path.insert(0, path)

# Export the FastAPI app for Vercel Serverless Functions
from ln.api import app
