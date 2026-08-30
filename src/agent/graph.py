"""LangGraph tool-calling agent.

When a PDF is loaded, a prefetch node runs ``search_documents`` before the
LLM so a 3B router cannot skip retrieval and ask for more context. The agent
node then answers from those passages (or calls more tools). A prebuilt
ToolNode executes any further tool calls and loops back until the model
produces a final answer.
"""

from __future__ import annotations

import logging
import re
import uuid
from typing import Any

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from src.agent.tools import get_tools
from src.agent.tools.search_documents import search_documents
from src.config import AGENT_HISTORY_TURNS
from src.llm import get_llm

logger = logging.getLogger(__name__)

_agent = None

# Corpus-inventory questions belong on sql_metadata_query, not PDF search.
_METADATA_HINTS = (
    "how many document",
    "how many pdf",
    "how many file",
    "how many page",
    "how many chunk",
    "list document",
    "list the file",
    "what documents",
    "which documents",
    "what files are",
    "files loaded",
    "documents loaded",
    "documents are loaded",
    "ingest date",
    "when was this uploaded",
    "when were they ingested",
)
_ARITH_PREFIX = re.compile(
    r"^(?:what(?:'s| is)|calculate|compute|eval(?:uate)?)\s+",
    re.IGNORECASE,
)
_ARITH_BODY = re.compile(r"^[\d\s+\-*/().%^,]+$")


def _loaded_filenames() -> list[str]:
    try:
        from src.metadata import list_documents

        return [str(row["filename"]) for row in list_documents() if row.get("filename")]
    except Exception:  # noqa: BLE001
        return []


def _skip_document_search(text: str) -> bool:
    """True for math or corpus-metadata questions that should not prefetch PDF search."""
    t = text.strip().lower()
    if not t:
        return True
    if any(hint in t for hint in _METADATA_HINTS):
        return True
    body = _ARITH_PREFIX.sub("", t).strip()
    return bool(_ARITH_BODY.fullmatch(body))


def _system_message() -> SystemMessage:
    """Build a per-request system prompt that names the session corpus."""
    names = _loaded_filenames()
    if names:
        loaded = "Documents currently loaded: " + ", ".join(names) + "."
        search_rule = (
            "Never ask the user to paste, upload, or name the document. "
            "Never ask which document they mean when files are already loaded. "
            "Pronouns like 'it', 'this', 'the document', and 'here' refer to "
            "the loaded files. If search_documents results are already in this "
            "conversation, answer from those passages: extract emails, names, "
            "and other facts instead of asking for more context. Only call "
            "search_documents again if you need a different query. If the "
            "passages do not contain the answer, say so; then use web_search "
            "if it is available."
        )
    else:
        loaded = "No documents are loaded in this session."
        search_rule = (
            "If the user asks about document content, still call "
            "search_documents; it will report when nothing is ingested."
        )

    return SystemMessage(
        content=(
            "You are Riffle, an assistant that answers questions about the user's "
            "uploaded documents. "
            f"{loaded}\n"
            f"{search_rule}\n"
            "Use the available tools:\n"
            "- search_documents: search the uploaded documents. PREFER THIS FIRST "
            "for any question about document content.\n"
            "- calculator: evaluate arithmetic. Always use it for math rather than "
            "computing in your head.\n"
            "- sql_metadata_query: read-only SQL about which documents have been "
            "ingested (counts, page totals, ingest dates).\n"
            "- web_search (only if available): public-web fallback, used ONLY when "
            "the documents do not contain the answer.\n\n"
            "Ground answers in tool results. If the documents lack the answer and "
            "web search is unavailable, say you do not know based on the uploaded "
            "documents. Keep answers concise."
        )
    )


def _history_messages(
    message: str, history: list[dict[str, Any]] | None
) -> list[BaseMessage]:
    """Prior turns plus the current question (deduped if already last)."""
    out: list[BaseMessage] = []
    for turn in (history or [])[-AGENT_HISTORY_TURNS:]:
        role = str(turn.get("role") or "").lower()
        content = str(turn.get("content") or "").strip()
        if not content:
            continue
        if role == "user":
            out.append(HumanMessage(content=content))
        elif role == "assistant":
            out.append(AIMessage(content=content))

    current = message.strip()
    if not out or not (
        isinstance(out[-1], HumanMessage) and out[-1].content == current
    ):
        out.append(HumanMessage(content=current))
    return out


def _prefetch_search(state: MessagesState) -> dict:
    """Run document search before the LLM so retrieval cannot be skipped."""
    from src import retrieval

    last_human = ""
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            last_human = str(msg.content or "")
            break

    if not retrieval.is_loaded() or _skip_document_search(last_human):
        return {}

    query = last_human.strip()
    call_id = f"prefetch-{uuid.uuid4().hex[:12]}"
    result = search_documents.invoke({"query": query})
    logger.info("Prefetched search_documents for query %r", query[:80])
    return {
        "messages": [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "search_documents",
                        "args": {"query": query},
                        "id": call_id,
                        "type": "tool_call",
                    }
                ],
            ),
            ToolMessage(
                content=str(result),
                tool_call_id=call_id,
                name="search_documents",
            ),
        ]
    }


def _build():
    llm = get_llm()
    tools = get_tools()
    llm_with_tools = llm.bind_tools(tools)

    def agent_node(state: MessagesState) -> dict:
        # System prompt is rebuilt each call so the loaded-file list stays current.
        response = llm_with_tools.invoke([_system_message()] + state["messages"])
        return {"messages": [response]}

    def should_continue(state: MessagesState):
        last = state["messages"][-1]
        if getattr(last, "tool_calls", None):
            return "tools"
        return END

    builder = StateGraph(MessagesState)
    builder.add_node("prefetch", _prefetch_search)
    builder.add_node("agent", agent_node)
    builder.add_node("tools", ToolNode(tools))
    builder.add_edge(START, "prefetch")
    builder.add_edge("prefetch", "agent")
    builder.add_conditional_edges("agent", should_continue, ["tools", END])
    builder.add_edge("tools", "agent")
    return builder.compile()


def get_agent():
    global _agent
    if _agent is None:
        _agent = _build()
        logger.info("Built LangGraph agent with %d tools.", len(get_tools()))
    return _agent


def _tool_path(messages: list) -> list[str]:
    """Ordered list of tool names the agent invoked, as they were called."""
    path: list[str] = []
    for msg in messages:
        for call in getattr(msg, "tool_calls", None) or []:
            name = call.get("name") if isinstance(call, dict) else getattr(call, "name", None)
            if name:
                path.append(name)
    return path


def answer(message: str, history: list[dict[str, Any]] | None = None) -> str:
    """Run the agent to completion and return the final text answer."""
    return answer_detailed(message, history=history)["answer"]


def answer_detailed(
    message: str, history: list[dict[str, Any]] | None = None
) -> dict:
    """Run the agent and report the answer alongside how it was reached.

    Returns the final text plus the ordered tool-call path and the passages the
    ``search_documents`` tool actually returned (with rerank scores).
    """
    if not message or not message.strip():
        raise ValueError("Message must not be empty")

    from src.agent import trace
    from src.tracing import traced_run

    sources = trace.start_capture()
    try:
        with traced_run("riffle_agent"):
            result = get_agent().invoke(
                {"messages": _history_messages(message, history)},
                {"run_name": "riffle_agent", "tags": ["riffle"]},
            )
    finally:
        trace.stop_capture()

    messages = result["messages"]
    final = messages[-1]
    return {
        "answer": getattr(final, "content", str(final)),
        "tool_path": _tool_path(messages),
        "sources": list(sources),
    }
