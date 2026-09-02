"""Cross-encoder reranking stage.

Takes the candidate pool from hybrid retrieval and reorders it with a
cross-encoder that scores each (query, passage) pair jointly - far more precise
than the first-stage bi-encoder similarity, which improves grounding and
reduces hallucination.
"""

from __future__ import annotations

import logging

from langchain_core.documents import Document

from src.config import RERANK_ENABLED, RERANKER_MODEL, RETRIEVER_K
from src.embeddings import get_torch_device

logger = logging.getLogger(__name__)

_cross_encoder = None


def _get_cross_encoder():
    global _cross_encoder
    if _cross_encoder is None:
        from sentence_transformers import CrossEncoder

        _cross_encoder = CrossEncoder(RERANKER_MODEL, device=get_torch_device())
    return _cross_encoder


def warmup() -> None:
    """Load the cross-encoder so the first query is not a cold start."""
    if RERANK_ENABLED:
        _get_cross_encoder()


def rerank_with_scores(
    query: str,
    documents: list[Document],
    top_k: int | None = None,
    *,
    enabled: bool | None = None,
) -> list[tuple[Document, float]]:
    """Rerank and return ``(document, score)`` pairs, best first.

    Scores are the raw cross-encoder logits. When reranking is disabled the
    original order is kept and scores are reported as ``None``-equivalent 0.0,
    so callers can still render a consistent shape.
    """
    k = top_k or RETRIEVER_K
    use_rerank = RERANK_ENABLED if enabled is None else enabled
    if not use_rerank or not documents:
        return [(doc, 0.0) for doc in documents[:k]]

    model = _get_cross_encoder()
    pairs = [(query, doc.page_content) for doc in documents]
    scores = model.predict(pairs)

    ranked = sorted(zip(documents, scores), key=lambda x: x[1], reverse=True)
    return [(doc, float(score)) for doc, score in ranked[:k]]
