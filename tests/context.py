# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Marcel Petrick <mail@marcelpetrick.it>
"""Make the crawler package and run.py importable from the tests.

crawler/ is a plain script directory, not an installed package, so the tests
put it on sys.path the same way the scripts find each other at runtime.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_RAW = REPO_ROOT / "tests" / "fixtures" / "raw"

for entry in (REPO_ROOT, REPO_ROOT / "crawler"):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

__all__ = ["REPO_ROOT", "FIXTURE_RAW"]
