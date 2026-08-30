from __future__ import annotations

import time
from pathlib import Path

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate

from src import retrieval
from src.config import RETRIEVER_K
from src.ingest import load_and_split_pdf
from src.llm import get_llm

_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful assistant that answers questions using only the "
            "provided document context. If the answer is not in the context, say "
            "you do not know based on the uploaded document.\n\nContext:\n{context}",
        ),
        ("human", "{question}"),
    ]
)


class DocumentNotLoadedError(RuntimeError):
    """Raised when chat is requested before any document has been ingested."""


def _format_docs(docs: list[Document]) -> str:
    return "\n\n".join(doc.page_content for doc in docs)


def process_document(path: str | Path) -> dict:
    """Ingest a PDF into the current session index (appends; same file replaces)."""
    chunks = load_and_split_pdf(path)
    if not chunks:
        raise ValueError("No text could be extracted from the PDF")

    retrieval.add_chunks(chunks)

    filename = Path(path).name
    try:
        from src.metadata import record_document

        record_document(path, chunk_count=len(chunks))
    except Exception:  # noqa: BLE001 - metadata store is optional (Phase 4)
        pass

    return {"ok": True, "chunks": len(chunks), "filename": filename}


def _handle_llm_error(exc: Exception) -> None:
    err = str(exc).lower()
    if "connection" in err or "connect" in err or "refused" in err:
        from src.config import LLAMA_BASE_URL, LLAMA_MODEL

        raise ConnectionError(
            f"Cannot reach LLM at {LLAMA_BASE_URL} (model={LLAMA_MODEL}). "
            "Start Ollama (`ollama serve`) and ensure the model is pulled "
            f"(e.g. `ollama pull {LLAMA_MODEL}`)."
        ) from exc
    raise exc


def get_context(message: str) -> list[Document]:
    """Retrieve the grounding chunks for a message (shared with the agent)."""
    return retrieval.retrieve(message.strip(), top_k=RETRIEVER_K)


def answer_with_sources(message: str) -> tuple[str, list[Document]]:
    """Generate a grounded answer and return it with the contexts used.

    Retrieving once and generating from the same contexts keeps the answer and
    its supporting passages consistent (important for faithful evaluation).
    """
    if not message or not message.strip():
        raise ValueError("Message must not be empty")
    if not retrieval.is_loaded():
        raise DocumentNotLoadedError(
            "No document loaded. Upload and ingest a PDF first."
        )

    docs = get_context(message)
    chain = _PROMPT | get_llm()
    try:
        result = chain.invoke(
            {"context": _format_docs(docs), "question": message.strip()}
        )
    except Exception as exc:  # noqa: BLE001
        _handle_llm_error(exc)
    return getattr(result, "content", str(result)), docs


def process_prompt(message: str, history: list | None = None) -> str:
    """Answer a question and return just the text.

    Routes through the LangGraph agent (tool-calling over document search,
    calculator, SQL metadata, and optional web search) when the agent is
    enabled; otherwise falls back to the plain RAG chain.
    """
    return process_prompt_detailed(message, history=history)["answer"]


def _confidence(top_score: float | None) -> str:
    """Coarse confidence label derived from the top cross-encoder score.

    Heuristic only: cross-encoder logits are unbounded, so these thresholds are
    a readable proxy rather than a calibrated probability.
    """
    if top_score is None:
        return "Unknown"
    if top_score >= 5.0:
        return "High"
    if top_score >= 0.0:
        return "Medium"
    return "Low"


def process_prompt_detailed(message: str, history: list | None = None) -> dict:
    """Answer a question and report how the answer was produced.

    Returns ``{answer, sources, tool_path, metrics}`` where ``sources`` are the
    retrieved passages with rerank scores, ``tool_path`` is the ordered list of
    tools the agent called, and ``metrics`` summarises the run.
    """
    if not message or not message.strip():
        raise ValueError("Message must not be empty")

    from src.config import AGENT_ENABLED

    started = time.perf_counter()
    answer: str
    sources: list[dict]
    tool_path: list[str]

    if AGENT_ENABLED:
        from src.agent import graph

        try:
            detailed = graph.answer_detailed(message, history=history)
        except Exception as exc:  # noqa: BLE001
            _handle_llm_error(exc)
        answer = detailed["answer"]
        tool_path = detailed["tool_path"]
        sources = detailed["sources"]

        # Only show sources the agent actually retrieved. Metadata/math answers
        # should not backfill unrelated chunks into the sources panel.
        if "search_documents" not in tool_path:
            sources = []
    else:
        tool_path = []
        if not retrieval.is_loaded():
            raise DocumentNotLoadedError(
                "No document loaded. Upload and ingest a PDF first."
            )
        from src.agent.trace import to_source

        scored = retrieval.retrieve_with_scores(message.strip())
        chain = _PROMPT | get_llm()
        try:
            from src.tracing import traced_run

            with traced_run("riffle_rag"):
                result = chain.invoke(
                    {
                        "context": _format_docs([doc for doc, _ in scored]),
                        "question": message.strip(),
                    }
                )
        except Exception as exc:  # noqa: BLE001
            _handle_llm_error(exc)
        answer = getattr(result, "content", str(result))
        sources = [to_source(doc, score) for doc, score in scored]

    latency_s = round(time.perf_counter() - started, 2)
    top_score = max((s["score"] for s in sources), default=None) if sources else None
    searched = "search_documents" in tool_path or not AGENT_ENABLED

    return {
        "answer": answer,
        "sources": sources,
        "tool_path": tool_path,
        "metrics": {
            "grounded": bool(sources) and searched,
            "sources_used": len(sources),
            "confidence": _confidence(top_score),
            "latency_s": latency_s,
        },
    }


def is_document_loaded() -> bool:
    return retrieval.is_loaded()
