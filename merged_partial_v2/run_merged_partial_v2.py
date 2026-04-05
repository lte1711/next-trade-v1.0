"""Launcher for the merged partial integration workspace."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from merged_partial_v2.main import main


if __name__ == "__main__":
    main()
