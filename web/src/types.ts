export type Role = "user" | "assistant";

/** A retrieved passage supporting an answer. */
export interface Source {
  title: string;
  location?: string | null;
  snippet: string;
  score: number;
}

/** Summary of how an answer was produced. */
export interface Metrics {
  grounded: boolean;
  sourcesUsed: number;
  confidence: string;
  latencyS: number;
}

export interface ChatMessage {
  id: string;
  role: Role;
  content: string;
  /** Clock time the message was added, for the mono timestamp. */
  at: string;
  /** For voice questions: what STT heard. */
  transcript?: string;
  /** For assistant answers spoken back: object URL of the WAV. */
  audioUrl?: string;
  /** Retrieval + agent detail attached to assistant turns. */
  sources?: Source[];
  toolPath?: string[];
  metrics?: Metrics;
  pending?: boolean;
  failed?: boolean;
}

export function uid(): string {
  return Math.random().toString(36).slice(2) + Date.now().toString(36);
}

export function nowLabel(): string {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}
