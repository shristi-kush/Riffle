"""Shared embedding model provider.

Centralised so the ingest-time chunker, the vector store, and the semantic
chunker all reuse a single cached model instance instead of reloading it.
"""

from __future__ import annotations

from langchain_huggingface import HuggingFaceEmbeddings

from src.config import BGE_QUERY_INSTRUCTION, EMBEDDING_DEVICE, EMBEDDING_MODEL

_embeddings: HuggingFaceEmbeddings | None = None


def get_torch_device() -> str:
    """Resolve ``auto`` to cuda when a GPU is visible, otherwise cpu."""
    raw = (EMBEDDING_DEVICE or "auto").strip().lower()
    if raw and raw != "auto":
        return raw
    try:
        import torch

        if torch.cuda.is_available():
            return "cuda"
    except Exception:  # noqa: BLE001
        pass
    return "cpu"


def get_embeddings() -> HuggingFaceEmbeddings:
    """Return a cached HuggingFace embedding model.

    BGE-family models perform best when queries (but not documents) are
    prefixed with a short instruction, so a query-side prompt is applied when
    the configured model looks like a BGE model.
    """
    global _embeddings
    if _embeddings is not None:
        return _embeddings

    device = get_torch_device()
    encode_kwargs = {"normalize_embeddings": True}
    model_kwargs = {"device": device}

    if "bge" in EMBEDDING_MODEL.lower():
        _embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs=model_kwargs,
            encode_kwargs=encode_kwargs,
            query_encode_kwargs={
                "prompt": BGE_QUERY_INSTRUCTION,
                "normalize_embeddings": True,
            },
        )
    else:
        _embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs=model_kwargs,
            encode_kwargs=encode_kwargs,
        )
    return _embeddings


def warmup_embeddings() -> None:
    get_embeddings().embed_query("warmup")
