"""Web search tool (Tavily) - optional, documents-first fallback.

Auto-disabled when ``TAVILY_API_KEY`` is not set, in which case the tool is not
registered with the agent at all (see ``tools.get_tools``). The ``@tool``
wrapper here still exists so imports are stable.
"""

from __future__ import annotations

from langchain_core.tools import tool

from src.config import TAVILY_API_KEY, WEB_SEARCH_MAX_RESULTS

_client = None


def web_search_available() -> bool:
    return bool(TAVILY_API_KEY)


def _get_client():
    global _client
    if _client is None:
        from langchain_tavily import TavilySearch

        _client = TavilySearch(
            max_results=WEB_SEARCH_MAX_RESULTS,
            topic="general",
            tavily_api_key=TAVILY_API_KEY,
        )
    return _client


@tool
def web_search(query: str) -> str:
    """Search the public web for current facts or information missing from the documents.

    Call this when the question needs live data (stock prices, news, weather,
    today's events) or when search_documents did not contain the answer. Do not
    claim this tool is unavailable — if you can call it, it is configured.
    """
    if not web_search_available():
        return (
            "Web search is not configured (TAVILY_API_KEY is not set). "
            "Answer from the documents or general knowledge instead."
        )
    try:
        result = _get_client().invoke({"query": query})
    except Exception as exc:  # noqa: BLE001
        return f"Web search failed: {exc}"
    return str(result)
