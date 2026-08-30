#!/usr/bin/env python
"""Convenience entry point for the evaluation harness.

Equivalent to ``python -m src.evaluation`` (held-out RAGAS + retrieval
ablation). Requires Ollama running with the chat/eval model pulled, plus the
sample PDFs generated via ``python scripts/make_sample_docs.py``.

    python scripts/run_eval.py
    python scripts/run_eval.py --all          # also run the easy smoke quiz
    python scripts/run_retrieval_ablation.py  # hit rates only, no judge LLM
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.evaluation import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
