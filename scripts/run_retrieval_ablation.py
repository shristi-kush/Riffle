#!/usr/bin/env python
"""Run the retrieval-only ablation (source hit rates, no RAGAS judge).

Equivalent to ``python -m src.evaluation --ablation``.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.evaluation import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main(["--ablation"]))
