#!/usr/bin/env python3
"""Run repo-miner from this folder without installing it: python3 mine.py <repository | folder | git URL>"""
import sys
from pathlib import Path

if sys.version_info < (3, 9):
    sys.exit("repo-miner needs Python 3.9 or newer")
sys.path.insert(0, str(Path(__file__).resolve().parent))

from repo_miner.cli import main  # noqa: E402

sys.exit(main())
