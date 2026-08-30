"""Session-scoped corpus: wipe index, metadata, uploads, and answer audio."""

from __future__ import annotations

import logging
from pathlib import Path

from src import metadata, retrieval
from src.config import DATA_RAW_DIR, TTS_VOICE_DIR, VOICE_DIR

logger = logging.getLogger(__name__)


def reset_corpus() -> dict:
    """Start a clean corpus: no documents, no leftover session audio.

    Piper voice models under ``data/voice/piper`` are kept.
    """
    try:
        retrieval.reset_index()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Index reset failed: %s", exc)
    try:
        metadata.reset_store()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Metadata reset failed: %s", exc)
    pdfs_removed = _delete_files(DATA_RAW_DIR, "*.pdf")
    audio_removed = _clear_session_audio()
    logger.info(
        "Reset session corpus (removed %d pdfs, %d answer wavs).",
        pdfs_removed,
        audio_removed,
    )
    return {
        "ok": True,
        "pdfs_removed": pdfs_removed,
        "audio_removed": audio_removed,
    }


def _delete_files(directory: Path, pattern: str) -> int:
    removed = 0
    if not directory.is_dir():
        return 0
    for path in directory.glob(pattern):
        if not path.is_file():
            continue
        try:
            path.unlink()
            removed += 1
        except OSError as exc:
            logger.warning("Could not delete %s: %s", path, exc)
    return removed


def _clear_session_audio() -> int:
    """Delete synthesized answer WAVs; never touch Piper models."""
    removed = 0
    if not VOICE_DIR.is_dir():
        return 0
    for path in VOICE_DIR.iterdir():
        if not path.is_file():
            continue
        if path.suffix.lower() != ".wav":
            continue
        # Keep anything inside the Piper voice dir; only session answers.
        try:
            path.resolve().relative_to(TTS_VOICE_DIR.resolve())
            continue
        except ValueError:
            pass
        try:
            path.unlink()
            removed += 1
        except OSError as exc:
            logger.warning("Could not delete %s: %s", path, exc)
    return removed
