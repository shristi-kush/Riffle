from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request

from langchain_openai import ChatOpenAI

from src.config import (
    LLAMA_API_KEY,
    LLAMA_BASE_URL,
    LLAMA_MODEL,
    LLM_KEEP_ALIVE,
    LLM_MAX_TOKENS,
    LLM_NUM_CTX,
)

logger = logging.getLogger(__name__)

_llm: ChatOpenAI | None = None


def _ollama_root() -> str:
    """Strip the OpenAI-compat ``/v1`` suffix so we can hit native Ollama APIs."""
    return LLAMA_BASE_URL.rstrip("/").removesuffix("/v1")


def _keep_alive() -> int | str:
    try:
        return int(LLM_KEEP_ALIVE)
    except ValueError:
        return LLM_KEEP_ALIVE


def init_llm() -> ChatOpenAI:
    """Create and cache the private Llama chat client (OpenAI-compatible API)."""
    global _llm
    _llm = ChatOpenAI(
        base_url=LLAMA_BASE_URL,
        api_key=LLAMA_API_KEY,
        model=LLAMA_MODEL,
        temperature=0.1,
        max_tokens=LLM_MAX_TOKENS,
        extra_body={
            "keep_alive": _keep_alive(),
            "options": {
                "num_ctx": LLM_NUM_CTX,
                "num_predict": LLM_MAX_TOKENS,
            },
        },
    )
    return _llm


def get_llm() -> ChatOpenAI:
    if _llm is None:
        raise RuntimeError("LLM not initialized. Call init_llm() first.")
    return _llm


def warmup_llm() -> None:
    """Load the Ollama weights so the first user question is not a cold start."""
    payload = json.dumps(
        {
            "model": LLAMA_MODEL,
            "prompt": "OK",
            "stream": False,
            "keep_alive": _keep_alive(),
            "options": {"num_predict": 1, "num_ctx": LLM_NUM_CTX},
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{_ollama_root()}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            resp.read()
        logger.info("Warmed Ollama model %s (keep_alive=%s).", LLAMA_MODEL, LLM_KEEP_ALIVE)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        logger.warning("LLM warmup skipped (%s). First chat may be slow.", exc)
