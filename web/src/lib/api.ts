// Typed wrappers around the Riffle FastAPI backend.
// VITE_API_BASE is empty by default so requests are same-origin (FastAPI serves
// the built SPA). For local dev, set VITE_API_BASE=http://localhost:5000.

import type { Metrics, Source } from "../types";

const API_BASE = (import.meta.env.VITE_API_BASE ?? "").replace(/\/$/, "");

const url = (path: string) => `${API_BASE}${path}`;

export interface IngestResult {
  ok: boolean;
  filename: string;
  chunks: number;
}

export interface AnswerDetail {
  answer: string;
  sources: Source[];
  toolPath: string[];
  metrics: Metrics;
}

export interface VoiceChatResult extends AnswerDetail {
  transcript: string;
  /** Object URL for the synthesized WAV; revoke when done. */
  audioUrl: string;
}

interface RawMetrics {
  grounded: boolean;
  sources_used: number;
  confidence: string;
  latency_s: number;
}

interface RawAnswer {
  answer: string;
  sources: Source[];
  tool_path: string[];
  metrics: RawMetrics;
}

async function readError(res: Response): Promise<string> {
  try {
    const data = await res.json();
    if (data && typeof data.detail === "string") return data.detail;
    return JSON.stringify(data);
  } catch {
    return `${res.status} ${res.statusText}`;
  }
}

function toDetail(data: RawAnswer): AnswerDetail {
  return {
    answer: data.answer,
    sources: data.sources ?? [],
    toolPath: data.tool_path ?? [],
    metrics: {
      grounded: data.metrics.grounded,
      sourcesUsed: data.metrics.sources_used,
      confidence: data.metrics.confidence,
      latencyS: data.metrics.latency_s,
    },
  };
}

export async function checkHealth(signal?: AbortSignal): Promise<boolean> {
  try {
    const res = await fetch(url("/health"), { signal });
    if (!res.ok) return false;
    const data = await res.json();
    return data?.status === "ok";
  } catch {
    return false;
  }
}

export async function ingestPdf(file: File): Promise<IngestResult> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(url("/ingest"), { method: "POST", body: form });
  if (!res.ok) throw new Error(await readError(res));
  return res.json();
}

export interface CorpusDocument {
  filename: string;
  pages: number;
  chunks: number;
  ingestedAt: string;
}

export async function fetchCorpus(): Promise<CorpusDocument[]> {
  const res = await fetch(url("/corpus"));
  if (!res.ok) throw new Error(await readError(res));
  const data = await res.json();
  return (data.documents ?? []).map(
    (row: { filename: string; pages: number; chunks: number; ingested_at: string }) => ({
      filename: row.filename,
      pages: row.pages,
      chunks: row.chunks,
      ingestedAt: row.ingested_at,
    })
  );
}

export async function resetSession(): Promise<void> {
  const res = await fetch(url("/reset"), { method: "POST" });
  if (!res.ok) throw new Error(await readError(res));
}

export interface ChatTurn {
  role: "user" | "assistant";
  content: string;
}

export async function sendChat(
  message: string,
  history: ChatTurn[] = []
): Promise<AnswerDetail> {
  const res = await fetch(url("/chat"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, history }),
  });
  if (!res.ok) throw new Error(await readError(res));
  return toDetail(await res.json());
}

function base64ToBlobUrl(base64: string, mime = "audio/wav"): string {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return URL.createObjectURL(new Blob([bytes], { type: mime }));
}

export async function sendVoice(
  file: Blob,
  filename = "question.wav",
  history: ChatTurn[] = []
): Promise<VoiceChatResult> {
  const form = new FormData();
  form.append("file", file, filename);
  if (history.length) {
    form.append("history", JSON.stringify(history));
  }
  const res = await fetch(url("/voice-chat"), { method: "POST", body: form });
  if (!res.ok) throw new Error(await readError(res));
  const data = await res.json();
  return {
    ...toDetail(data),
    transcript: data.transcript,
    audioUrl: base64ToBlobUrl(data.audio_base64),
  };
}
