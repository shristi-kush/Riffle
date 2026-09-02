"""LangGraph tool-calling agent.

When a PDF is loaded, a prefetch node runs ``search_documents`` before the
LLM so a 3B router cannot skip retrieval and ask for more context. Live or
current-event questions also prefetch ``web_search`` (when Tavily is
configured) for the same reason: a small router will otherwise answer from
the PDF and never call the tool. If the model still replies that the
documents miss, a fallback node forces ``web_search`` and loops back.

After prefetch (or a forced web search), a compose node writes the final
answer *without* tool schemas — one generation instead of a tool-calling
round trip. Math and corpus-metadata questions skip prefetch and still use
the tool-calling agent.
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
from src.agent.tools.web_search import web_search, web_search_available
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

# Questions a 3B router will not promote to web_search on its own.
_EXPLICIT_WEB = (
    "search the web",
    "search online",
    "look online",
    "look it up online",
    "from the internet",
    "from the web",
    "web search",
    "browse the web",
    "on the internet",
    "google it",
)
_LIVE_TOPIC = re.compile(
    r"\b("
    r"stock prices?|share prices?|ticker(?: symbol)?|"
    r"trading at|market cap|"
    r"weather|forecast|"
    r"(?:latest|breaking|today'?s) news|headlines?|"
    r"exchange rates?|"
    r"bitcoin|ethereum|crypto(?:currency)? prices?"
    r")\b",
    re.IGNORECASE,
)
_CURRENT_LIVE = re.compile(
    r"\bcurrent(?:ly)?\s+"
    r"(?:stock|share|price|ceo|president|weather|news|market)\b",
    re.IGNORECASE,
)
_TIME_SENSITIVE = re.compile(
    r"\b("
    r"today|tonight|right now|as of now|as of today|"
    r"this (?:morning|afternoon|evening)|"
    r"real[- ]?time"
    r")\b",
    re.IGNORECASE,
)
_LIVE_WITH_TIME = re.compile(
    r"\b(prices?|cost|worth|news|headline|weather|temperature|score)\b",
    re.IGNORECASE,
)
_MISS_HINTS = (
    "not mentioned",
    "not discussed",
    "not found in",
    "do not contain",
    "does not contain",
    "don't contain",
    "doesn't contain",
    "not in the document",
    "not in the provided",
    "no information",
    "web search is not",
    "web search tool",
    "not available within",
    "i do not know",
    "i don't know",
    "cannot determine",
    "can't determine",
    "unable to find",
    "the document does not",
    "the documents do not",
    "is not mentioned",
)


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


def _needs_web_search(text: str) -> bool:
    """True when the question is live/current or the user asked to search the web."""
    t = text.strip().lower()
    if not t:
        return False
    if any(hint in t for hint in _EXPLICIT_WEB):
        return True
    if _LIVE_TOPIC.search(t) or _CURRENT_LIVE.search(t):
        return True
    return bool(_TIME_SENSITIVE.search(t) and _LIVE_WITH_TIME.search(t))


def _looks_like_document_miss(text: str) -> bool:
    t = (text or "").strip().lower()
    return bool(t) and any(hint in t for hint in _MISS_HINTS)


def _document_search_empty(result: str) -> bool:
    t = (result or "").strip().lower()
    return (
        not t
        or "no relevant passages" in t
        or "no document has been ingested" in t
        or "nothing to search" in t
    )


def _last_human_text(messages: list[BaseMessage]) -> str:
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            return str(msg.content or "")
    return ""


def _tool_path(messages: list) -> list[str]:
    """Ordered list of tool names the agent invoked, as they were called."""
    path: list[str] = []
    for msg in messages:
        for call in getattr(msg, "tool_calls", None) or []:
            name = call.get("name") if isinstance(call, dict) else getattr(call, "name", None)
            if name:
                path.append(name)
    return path


def _synthetic_tool_turn(
    calls: list[tuple[str, dict, str]],
) -> list[BaseMessage]:
    """Build an AIMessage + ToolMessage(s) as if the model called these tools."""
    tool_calls = []
    tool_messages: list[BaseMessage] = []
    for name, args, result in calls:
        call_id = f"prefetch-{uuid.uuid4().hex[:12]}"
        tool_calls.append(
            {
                "name": name,
                "args": args,
                "id": call_id,
                "type": "tool_call",
            }
        )
        tool_messages.append(
            ToolMessage(
                content=str(result),
                tool_call_id=call_id,
                name=name,
            )
        )
    return [AIMessage(content="", tool_calls=tool_calls), *tool_messages]


def _system_message() -> SystemMessage:
    """Build a per-request system prompt that names the session corpus."""
    names = _loaded_filenames()
    web_on = web_search_available()
    if names:
        loaded = "Documents currently loaded: " + ", ".join(names) + "."
        search_rule = (
            "Never ask the user to paste, upload, or name the document. "
            "Never ask which document they mean when files are already loaded. "
            "Pronouns like 'it', 'this', 'the document', and 'here' refer to "
            "the loaded files. If search_documents results are already in this "
            "conversation, answer from those passages: extract emails, names, "
            "and other facts instead of asking for more context. Only call "
            "search_documents again if you need a different query."
        )
    else:
        loaded = "No documents are loaded in this session."
        search_rule = (
            "If the user asks about document content, still call "
            "search_documents; it will report when nothing is ingested."
        )

    if web_on:
        web_rule = (
            "web_search is configured and available. Use it for live/current "
            "facts (stock prices, news, weather, today's events) and whenever "
            "the uploaded documents do not contain the answer. If web_search "
            "results are already in this conversation, use them — never say "
            "web search is unavailable or that you cannot look the answer up."
        )
        web_tool = (
            "- web_search: AVAILABLE. Live/current facts and fallback when the "
            "documents miss. If its results are already present, use them."
        )
        miss_rule = (
            "If the documents lack the answer, call web_search (or use its "
            "results if they are already present) instead of stopping."
        )
    else:
        web_rule = "web_search is not configured in this session."
        web_tool = (
            "- web_search: not configured. Do not claim you will search the web."
        )
        miss_rule = (
            "If the documents lack the answer, say you do not know based on "
            "the uploaded documents."
        )

    return SystemMessage(
        content=(
            "You are Riffle, an assistant that answers questions about the user's "
            "uploaded documents and, when needed, the public web. "
            f"{loaded}\n"
            f"{search_rule}\n"
            f"{web_rule}\n"
            "Use the available tools:\n"
            "- search_documents: search the uploaded documents. PREFER THIS FIRST "
            "for any question about document content.\n"
            "- calculator: evaluate arithmetic. Always use it for math rather than "
            "computing in your head.\n"
            "- sql_metadata_query: read-only SQL about which documents have been "
            "ingested (counts, page totals, ingest dates).\n"
            f"{web_tool}\n\n"
            f"Ground answers in tool results. {miss_rule} Keep answers concise."
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
    """Run document search and, when needed, web search before the LLM.

    Live/current questions prefetch web_search so a 3B router cannot skip it.
    Empty document hits also prefetch web_search as a fallback.
    """
    from src import retrieval

    last_human = _last_human_text(state["messages"])
    if not last_human.strip():
        return {}

    query = last_human.strip()
    live = _needs_web_search(query)
    calls: list[tuple[str, dict, str]] = []

    want_docs = retrieval.is_loaded() and not _skip_document_search(query)
    # Live facts should not be answered from a stale PDF; skip doc prefetch so
    # the 3B model is not steered by unrelated chunks (e.g. a 10-K vs today's
    # stock price). The agent can still call search_documents if it needs to.
    if want_docs and not (live and web_search_available()):
        result = search_documents.invoke({"query": query})
        logger.info("Prefetched search_documents for query %r", query[:80])
        calls.append(("search_documents", {"query": query}, str(result)))
        if web_search_available() and _document_search_empty(str(result)):
            live = True

    if web_search_available() and live:
        result = web_search.invoke({"query": query})
        logger.info("Prefetched web_search for query %r", query[:80])
        calls.append(("web_search", {"query": query}, str(result)))

    if not calls:
        return {}
    return {"messages": _synthetic_tool_turn(calls)}


def _flatten_for_compose(
    messages: list[BaseMessage],
) -> tuple[list[BaseMessage], str]:
    """History plus concatenated tool results, without synthetic tool-call turns.

    ChatOpenAI/Ollama can choke on ``tool_calls`` in the history when tools are
    not bound, so compose uses a plain RAG-style prompt instead.
    """
    tool_blocks: list[str] = []
    history: list[BaseMessage] = []
    question = _last_human_text(messages)
    for msg in messages:
        if isinstance(msg, ToolMessage):
            name = getattr(msg, "name", None) or "tool"
            tool_blocks.append(f"[{name}]\n{msg.content}")
            continue
        if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
            continue
        if isinstance(msg, (HumanMessage, AIMessage)):
            history.append(msg)
    if (
        history
        and isinstance(history[-1], HumanMessage)
        and history[-1].content == question
    ):
        history = history[:-1]
    return history, "\n\n".join(tool_blocks)


def _compose_node(state: MessagesState) -> dict:
    """Write the final answer from already-fetched tool results (no extra LLM loop)."""
    messages = state["messages"]
    question = _last_human_text(messages)
    history, context = _flatten_for_compose(messages)
    names = _loaded_filenames()
    loaded = (
        "Documents currently loaded: " + ", ".join(names) + "."
        if names
        else "No documents are loaded in this session."
    )
    sys = SystemMessage(
        content=(
            "You are Riffle. Answer the user's question using only the tool "
            "results below. Extract emails, names, and other facts from them. "
            "If they do not contain the answer, say you do not know based on "
            "the uploaded documents. Keep answers concise.\n"
            f"{loaded}\n\nTool results:\n"
            f"{context or '(none)'}"
        )
    )
    response = get_llm().invoke([sys, *history, HumanMessage(content=question)])
    return {"messages": [response]}


def _after_prefetch(state: MessagesState) -> str:
    """Compose when prefetch already fetched context; otherwise use the tool-calling agent."""
    if any(isinstance(m, ToolMessage) for m in state["messages"]):
        return "compose"
    return "agent"


def _after_compose(state: MessagesState) -> str:
    if _should_force_web_search(state):
        return "web_fallback"
    return END


def _should_force_web_search(state: MessagesState) -> bool:
    """True when the model answered without searching the web but still needs it."""
    if not web_search_available():
        return False
    messages = state["messages"]
    last = messages[-1]
    if getattr(last, "tool_calls", None):
        return False
    if "web_search" in _tool_path(messages):
        return False
    query = _last_human_text(messages)
    if _skip_document_search(query) and not _needs_web_search(query):
        return False
    if _needs_web_search(query):
        return True
    content = str(getattr(last, "content", "") or "")
    return _looks_like_document_miss(content)


def _web_fallback(state: MessagesState) -> dict:
    """Force web_search after the model declined to call it."""
    query = _last_human_text(state["messages"]).strip()
    result = web_search.invoke({"query": query})
    logger.info("Forced web_search fallback for query %r", query[:80])
    return {
        "messages": _synthetic_tool_turn(
            [("web_search", {"query": query}, str(result))]
        )
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
        if _should_force_web_search(state):
            return "web_fallback"
        return END

    builder = StateGraph(MessagesState)
    builder.add_node("prefetch", _prefetch_search)
    builder.add_node("compose", _compose_node)
    builder.add_node("agent", agent_node)
    builder.add_node("tools", ToolNode(tools))
    builder.add_node("web_fallback", _web_fallback)
    builder.add_edge(START, "prefetch")
    builder.add_conditional_edges(
        "prefetch", _after_prefetch, ["compose", "agent"]
    )
    builder.add_conditional_edges(
        "compose", _after_compose, ["web_fallback", END]
    )
    builder.add_conditional_edges(
        "agent", should_continue, ["tools", "web_fallback", END]
    )
    builder.add_edge("tools", "agent")
    builder.add_edge("web_fallback", "compose")
    return builder.compile()


def get_agent():
    global _agent
    if _agent is None:
        _agent = _build()
        logger.info("Built LangGraph agent with %d tools.", len(get_tools()))
    return _agent


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
