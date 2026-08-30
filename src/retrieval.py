"""Hybrid retrieval: BM25 (sparse) + Chroma dense vectors via an ensemble.

Owns the in-memory index state (vector store + BM25 retriever) so that both
the RAG chain and the agent's ``search_documents`` tool share one index.
"""

from __future__ import annotations

import gc
import logging
import shutil
from pathlib import Path

try:  # LangChain 1.x moved EnsembleRetriever into langchain_classic
    from langchain_classic.retrievers import EnsembleRetriever
except ImportError:  # LangChain 0.x
    from langchain.retrievers import EnsembleRetriever

from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document

from src.config import (
    BM25_WEIGHT,
    CHROMA_DIR,
    COLLECTION_NAME,
    DENSE_WEIGHT,
    RETRIEVE_TOP_N,
    RETRIEVER_K,
)
from src.embeddings import get_embeddings

logger = logging.getLogger(__name__)

_vectorstore: Chroma | None = None
_bm25: BM25Retriever | None = None
_chunks: list[Document] = []
_documents_loaded = False


def _filename_of(doc: Document) -> str:
    return Path(str(doc.metadata.get("source", ""))).name


def _wipe_chroma_dir() -> None:
    import time

    if CHROMA_DIR.exists():
        for _ in range(5):
            shutil.rmtree(CHROMA_DIR, ignore_errors=True)
            if not CHROMA_DIR.exists():
                break
            gc.collect()
            time.sleep(0.15)
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)


def _rebuild_bm25() -> None:
    global _bm25, _documents_loaded
    if not _chunks:
        _bm25 = None
        _documents_loaded = False
        return
    _bm25 = BM25Retriever.from_documents(_chunks)
    _bm25.k = RETRIEVE_TOP_N
    _documents_loaded = True


def reset_index() -> None:
    """Drop the in-memory index and delete the persisted Chroma directory."""
    global _vectorstore, _bm25, _chunks, _documents_loaded

    if _vectorstore is not None:
        try:
            _vectorstore.delete_collection()
        except Exception:  # noqa: BLE001
            pass
        _vectorstore = None
    gc.collect()
    _wipe_chroma_dir()
    _bm25 = None
    _chunks = []
    _documents_loaded = False
    logger.info("Reset hybrid index.")


def add_chunks(chunks: list[Document]) -> None:
    """Append chunks to the current session index (replace a re-uploaded file)."""
    global _vectorstore, _chunks

    if not chunks:
        raise ValueError("No chunks to index")

    names = {_filename_of(c) for c in chunks if _filename_of(c)}
    if names:
        old_sources = {
            str(c.metadata.get("source"))
            for c in _chunks
            if _filename_of(c) in names and c.metadata.get("source")
        }
        _chunks = [c for c in _chunks if _filename_of(c) not in names]
        if _vectorstore is not None:
            for src in old_sources:
                try:
                    _vectorstore.delete(where={"source": src})
                except Exception:  # noqa: BLE001
                    logger.debug("Could not delete existing Chroma docs for %s", src)

    embeddings = get_embeddings()
    if _vectorstore is None:
        _wipe_chroma_dir()
        _vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=str(CHROMA_DIR),
            collection_name=COLLECTION_NAME,
        )
    else:
        _vectorstore.add_documents(chunks)

    _chunks.extend(chunks)
    _rebuild_bm25()
    logger.info(
        "Session index now has %d chunks from %d file(s).",
        len(_chunks),
        len({_filename_of(c) for c in _chunks if _filename_of(c)}),
    )


def build_index(chunks: list[Document]) -> None:
    """Replace the entire index with ``chunks`` (used by evaluation)."""
    reset_index()
    add_chunks(chunks)


def is_loaded() -> bool:
    return _documents_loaded


def get_hybrid_retriever(
    *,
    bm25_weight: float | None = None,
    dense_weight: float | None = None,
):
    """Return the configured retriever, optionally overriding ensemble weights.

    A weight of 0 skips that side so ablation can isolate BM25 vs dense.
    """
    if _vectorstore is None or _bm25 is None:
        raise RuntimeError("Index not built. Call build_index() first.")
    bw = BM25_WEIGHT if bm25_weight is None else bm25_weight
    dw = DENSE_WEIGHT if dense_weight is None else dense_weight
    dense = _vectorstore.as_retriever(search_kwargs={"k": RETRIEVE_TOP_N})
    _bm25.k = RETRIEVE_TOP_N
    if bw <= 0 and dw > 0:
        return dense
    if dw <= 0 and bw > 0:
        return _bm25
    return EnsembleRetriever(
        retrievers=[_bm25, dense],
        weights=[bw, dw],
    )


def retrieve_with_scores(
    query: str,
    top_k: int | None = None,
    *,
    bm25_weight: float | None = None,
    dense_weight: float | None = None,
    rerank_enabled: bool | None = None,
) -> list[tuple[Document, float]]:
    """Hybrid search plus reranking, returning ``(document, score)`` pairs.

    Exposing the cross-encoder score lets the UI show how strongly each passage
    supports the answer. When reranking is unavailable the hybrid order is kept
    and scores are reported as 0.0.
    """
    k = top_k or RETRIEVER_K
    candidates = get_hybrid_retriever(
        bm25_weight=bm25_weight, dense_weight=dense_weight
    ).invoke(query)

    try:
        from src.reranker import rerank_with_scores  # local import: optional (Phase 2)

        return rerank_with_scores(
            query, candidates, top_k=k, enabled=rerank_enabled
        )
    except Exception as exc:  # noqa: BLE001
        logger.debug("Reranking unavailable (%s); returning hybrid order.", exc)
        return [(doc, 0.0) for doc in candidates[:k]]


def retrieve(
    query: str,
    top_k: int | None = None,
    *,
    bm25_weight: float | None = None,
    dense_weight: float | None = None,
    rerank_enabled: bool | None = None,
) -> list[Document]:
    """Return the most relevant chunks for a query via hybrid search.

    A cross-encoder reranking stage is applied when enabled (Phase 2).
    """
    return [
        doc
        for doc, _ in retrieve_with_scores(
            query,
            top_k=top_k,
            bm25_weight=bm25_weight,
            dense_weight=dense_weight,
            rerank_enabled=rerank_enabled,
        )
    ]
