"""LangSmith tracing for the API process.

Env vars alone are not enough: LangSmith caches them, and FastAPI runs sync
``/chat`` in a threadpool. ``configure(enabled=True)`` plus a per-request
``trace`` parent makes agent runs show up in the project dashboard.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from contextlib import contextmanager

from src.config import LANGCHAIN_API_KEY, LANGCHAIN_PROJECT, LANGCHAIN_TRACING_V2

logger = logging.getLogger("uvicorn.error")


def tracing_active() -> bool:
    return bool(LANGCHAIN_TRACING_V2 and LANGCHAIN_API_KEY)


def init_tracing() -> None:
    """Force-enable LangSmith for this process after ``.env`` is loaded."""
    if not LANGCHAIN_TRACING_V2:
        return
    if not LANGCHAIN_API_KEY:
        return
    try:
        import langsmith as ls
        from langsmith import utils as ls_utils

        ls_utils.get_env_var.cache_clear()
        ls_utils.get_tracer_project.cache_clear()
        ls.configure(enabled=True, project_name=LANGCHAIN_PROJECT)
        logger.info("LangSmith tracing enabled (project=%s)", LANGCHAIN_PROJECT)
    except Exception as exc:  # noqa: BLE001
        logger.warning("LangSmith tracing could not be initialized: %s", exc)


@contextmanager
def traced_run(name: str) -> Iterator[None]:
    """Open a LangSmith parent run, attach LangChain callbacks, and flush."""
    if not tracing_active():
        yield
        return

    from langchain_core.tracers.context import tracing_v2_enabled
    from langchain_core.tracers.langchain import wait_for_all_tracers
    from langsmith import trace, tracing_context

    with tracing_context(enabled=True, project_name=LANGCHAIN_PROJECT):
        with tracing_v2_enabled(project_name=LANGCHAIN_PROJECT):
            with trace(name, run_type="chain", project_name=LANGCHAIN_PROJECT):
                try:
                    yield
                finally:
                    # Flush traces off the request path so LangSmith I/O does
                    # not add to the user-visible latency.
                    import threading

                    threading.Thread(
                        target=wait_for_all_tracers, daemon=True
                    ).start()
