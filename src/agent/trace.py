"""Per-request capture of the passages the agent actually retrieved.

The ``search_documents`` tool returns a plain string to the LLM, so the
supporting passages (and their rerank scores) would otherwise be lost. A
``ContextVar`` holding a mutable list lets the tool record what it returned
while the caller reads it back after the run.

The list object is created by the caller and mutated in place by the tool, which
is what makes this work when LangChain executes tools in a worker thread: the
thread inherits a *copy* of the context, but that copy still points at the same
list.
"""

from __future__ import annotations

from contextvars import ContextVar
from pathlib import Path
from typing import Any

from langchain_core.documents import Document

_SNIPPET_CHARS = 240

_sources_var: ContextVar[list[dict[str, Any]] | None] = ContextVar(
    "riffle_captured_sources", default=None
)


def to_source(doc: Document, score: float) -> dict[str, Any]:
    """Shape a retrieved chunk for the API/UI (title, location, snippet, score)."""
    raw_source = str(doc.metadata.get("source", "document"))
    title = Path(raw_source).name or raw_source

    page = doc.metadata.get("page")
    location = f"page {int(page) + 1}" if isinstance(page, (int, float)) else None

    text = (doc.page_content or "").strip().replace("\n", " ")
    snippet = text[:_SNIPPET_CHARS] + ("..." if len(text) > _SNIPPET_CHARS else "")

    return {"title": title, "location": location, "snippet": snippet, "score": score}


def start_capture() -> list[dict[str, Any]]:
    """Begin capturing for the current request and return the shared sink."""
    bucket: list[dict[str, Any]] = []
    _sources_var.set(bucket)
    return bucket


def stop_capture() -> None:
    _sources_var.set(None)


def record(pairs: list[tuple[Document, float]]) -> None:
    """Record ``(document, score)`` pairs if a capture is active."""
    bucket = _sources_var.get()
    if bucket is None:
        return
    seen = {(item["title"], item["snippet"]) for item in bucket}
    for doc, score in pairs:
        entry = to_source(doc, score)
        key = (entry["title"], entry["snippet"])
        if key not in seen:
            seen.add(key)
            bucket.append(entry)
