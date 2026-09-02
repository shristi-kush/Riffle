from __future__ import annotations

import base64
import json
import os
import tempfile
import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import FileResponse
from werkzeug.utils import secure_filename

from src.config import (
    BASE_DIR,
    DATA_RAW_DIR,
    LANGCHAIN_PROJECT,
    VOICE_DIR,
    warn_if_tracing_misconfigured,
)
from src.llm import init_llm, warmup_llm
from src.tracing import init_tracing, tracing_active
from src.rag import (
    DocumentNotLoadedError,
    is_document_loaded,
    process_document,
    process_prompt_detailed,
)
from src.session import reset_corpus

app = FastAPI(title="Riffle API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    warn_if_tracing_misconfigured()
    init_tracing()
    init_llm()
    reset_corpus()
    _warmup()


def _warmup() -> None:
    """Keep the Ollama weights resident so the first chat is not a cold load."""
    warmup_llm()


class ChatTurn(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: List[ChatTurn] = []


class Source(BaseModel):
    """A retrieved passage that supports the answer."""

    title: str
    location: Optional[str] = None
    snippet: str
    score: float


class Metrics(BaseModel):
    """Summary of how the answer was produced."""

    grounded: bool
    sources_used: int
    confidence: str
    latency_s: float


class ChatResponse(BaseModel):
    answer: str
    sources: List[Source]
    tool_path: List[str]
    metrics: Metrics


class IngestResponse(BaseModel):
    ok: bool
    filename: str
    chunks: int


class VoiceChatResponse(BaseModel):
    transcript: str
    answer: str
    audio_base64: str
    sources: List[Source]
    tool_path: List[str]
    metrics: Metrics


class CorpusDocument(BaseModel):
    filename: str
    pages: int
    chunks: int
    ingested_at: str


class CorpusResponse(BaseModel):
    loaded: bool
    documents: List[CorpusDocument]


class ResetResponse(BaseModel):
    ok: bool
    pdfs_removed: int
    audio_removed: int


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "langsmith": {
            "enabled": tracing_active(),
            "project": LANGCHAIN_PROJECT,
        },
    }


@app.get("/corpus", response_model=CorpusResponse)
def corpus() -> CorpusResponse:
    from src.metadata import list_documents

    docs = [
        CorpusDocument(
            filename=row["filename"],
            pages=int(row["page_count"]),
            chunks=int(row["chunk_count"]),
            ingested_at=str(row["ingest_date"]),
        )
        for row in list_documents()
    ]
    return CorpusResponse(loaded=is_document_loaded(), documents=docs)


@app.post("/reset", response_model=ResetResponse)
def reset() -> ResetResponse:
    result = reset_corpus()
    return ResetResponse(**result)


@app.post("/ingest", response_model=IngestResponse)
async def ingest(file: UploadFile = File(...)) -> IngestResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected")

    filename = secure_filename(file.filename)
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    dest = DATA_RAW_DIR / filename
    dest.write_bytes(await file.read())

    try:
        result = process_document(dest)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Ingest failed: {exc}") from exc

    return IngestResponse(
        ok=True, filename=result["filename"], chunks=result["chunks"]
    )


@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    if not payload.message or not payload.message.strip():
        raise HTTPException(
            status_code=400, detail="Body must include a non-empty 'message'"
        )

    try:
        result = process_prompt_detailed(
            payload.message,
            history=[
                turn.model_dump() if hasattr(turn, "model_dump") else turn.dict()
                for turn in payload.history
            ],
        )
    except DocumentNotLoadedError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Chat failed: {exc}") from exc

    return ChatResponse(**result)


@app.post("/voice-chat", response_model=VoiceChatResponse)
async def voice_chat(
    file: UploadFile = File(...),
    history: str = Form(default=""),
) -> VoiceChatResponse:
    """Voice in, voice out: transcribe -> answer -> synthesize speech."""
    from src.voice import stt, tts

    if not file.filename:
        raise HTTPException(status_code=400, detail="No audio file provided")

    suffix = Path(secure_filename(file.filename)).suffix or ".wav"
    tmp_in = Path(tempfile.gettempdir()) / f"riffle_in_{uuid.uuid4().hex}{suffix}"
    tmp_in.write_bytes(await file.read())

    turns: List[dict] = []
    if history and history.strip():
        try:
            parsed = json.loads(history)
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=400, detail="history must be a JSON array"
            ) from exc
        if isinstance(parsed, list):
            turns = [
                {"role": str(t.get("role", "")), "content": str(t.get("content", ""))}
                for t in parsed
                if isinstance(t, dict)
            ]

    try:
        transcript = stt.transcribe(tmp_in)
        if not transcript:
            raise HTTPException(status_code=400, detail="Could not transcribe audio")

        result = process_prompt_detailed(transcript, history=turns)
        answer = result["answer"]

        out_path = VOICE_DIR / f"answer_{uuid.uuid4().hex}.wav"
        tts.synthesize(answer, out_path)
        audio_b64 = base64.b64encode(out_path.read_bytes()).decode("ascii")
    except DocumentNotLoadedError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Voice chat failed: {exc}") from exc
    finally:
        tmp_in.unlink(missing_ok=True)

    return VoiceChatResponse(
        transcript=transcript,
        answer=answer,
        audio_base64=audio_b64,
        sources=result["sources"],
        tool_path=result["tool_path"],
        metrics=result["metrics"],
    )


# --- Static SPA (built React UI) ---------------------------------------------
# Mounted last so it never shadows the API routes above.

WEB_DIST = BASE_DIR / "web" / "dist"


class SPAStaticFiles(StaticFiles):
    """Serve the built SPA, falling back to index.html for client-side routes."""

    async def get_response(self, path: str, scope):  # type: ignore[override]
        try:
            return await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            if exc.status_code == 404:
                return FileResponse(Path(str(self.directory)) / "index.html")
            raise


if WEB_DIST.is_dir():
    app.mount("/", SPAStaticFiles(directory=WEB_DIST, html=True), name="spa")


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "5000"))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
