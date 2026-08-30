import { useCallback, useMemo, useState } from "react";
import ChatWindow from "../components/ChatWindow";
import Composer from "../components/Composer";
import DocumentsPanel from "../components/workspace/DocumentsPanel";
import GraphPathPanel from "../components/workspace/GraphPathPanel";
import IconRail, { type RailPanel } from "../components/workspace/IconRail";
import MetricsPanel from "../components/workspace/MetricsPanel";
import SessionBar from "../components/workspace/SessionBar";
import SourcesPanel from "../components/workspace/SourcesPanel";
import ToolsPanel from "../components/workspace/ToolsPanel";
import { sendChat, sendVoice, resetSession, type ChatTurn } from "../lib/api";
import { useRecorder } from "../lib/useRecorder";
import { nowLabel, uid, type ChatMessage } from "../types";

const SESSION_PLACEHOLDER = "New session";
const HISTORY_TURNS = 6;

function toHistory(messages: ChatMessage[]): ChatTurn[] {
  return messages
    .filter((m) => !m.pending && !m.failed && m.content.trim())
    .map((m) => ({
      role: m.role,
      content: (m.transcript || m.content).trim(),
    }))
    .slice(-HISTORY_TURNS);
}

export default function Workspace() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [busy, setBusy] = useState(false);
  const [panel, setPanel] = useState<RailPanel>("documents");
  const [docCount, setDocCount] = useState(0);
  const [sessionKey, setSessionKey] = useState(0);
  const [sessionError, setSessionError] = useState<string | null>(null);

  /** Side panels reflect the most recent completed assistant turn. */
  const latest = useMemo(
    () => [...messages].reverse().find((m) => m.role === "assistant" && !m.pending),
    [messages]
  );

  const sessionTitle = useMemo(() => {
    const first = messages.find((m) => m.role === "user");
    if (!first) return SESSION_PLACEHOLDER;
    const text = first.transcript || first.content;
    return text.length > 48 ? `${text.slice(0, 48)}...` : text;
  }, [messages]);

  const settle = useCallback((id: string, patch: Partial<ChatMessage>) => {
    setMessages((prev) =>
      prev.map((m) => (m.id === id ? { ...m, pending: false, ...patch } : m))
    );
  }, []);

  const handleText = useCallback(
    async (text: string) => {
      const history = toHistory(messages);
      setBusy(true);
      const pendingId = uid();
      setMessages((prev) => [
        ...prev,
        { id: uid(), role: "user", content: text, at: nowLabel() },
        { id: pendingId, role: "assistant", content: "", at: nowLabel(), pending: true },
      ]);
      try {
        const res = await sendChat(text, history);
        settle(pendingId, {
          content: res.answer,
          sources: res.sources,
          toolPath: res.toolPath,
          metrics: res.metrics,
        });
      } catch (e) {
        settle(pendingId, {
          content: e instanceof Error ? e.message : "Something went wrong.",
          failed: true,
        });
      } finally {
        setBusy(false);
      }
    },
    [settle, messages]
  );

  const handleVoice = useCallback(
    async (audio: Blob, filename: string) => {
      const history = toHistory(messages);
      setBusy(true);
      const userId = uid();
      const pendingId = uid();
      setMessages((prev) => [
        ...prev,
        { id: userId, role: "user", content: "Voice question", at: nowLabel() },
        { id: pendingId, role: "assistant", content: "", at: nowLabel(), pending: true },
      ]);
      try {
        const res = await sendVoice(audio, filename, history);
        setMessages((prev) =>
          prev.map((m) => {
            if (m.id === userId) {
              return { ...m, content: res.transcript, transcript: res.transcript };
            }
            if (m.id === pendingId) {
              return {
                ...m,
                pending: false,
                content: res.answer,
                audioUrl: res.audioUrl,
                sources: res.sources,
                toolPath: res.toolPath,
                metrics: res.metrics,
              };
            }
            return m;
          })
        );
      } catch (e) {
        settle(pendingId, {
          content: e instanceof Error ? e.message : "Something went wrong.",
          failed: true,
        });
      } finally {
        setBusy(false);
      }
    },
    [settle, messages]
  );

  const recorder = useRecorder({ onComplete: handleVoice });

  const onCorpusChange = useCallback((count: number) => {
    setDocCount(count);
  }, []);

  const endSession = useCallback(async () => {
    setSessionError(null);
    try {
      await resetSession();
    } catch (e) {
      setSessionError(e instanceof Error ? e.message : "Could not reset session.");
      return;
    }
    messages.forEach((m) => m.audioUrl && URL.revokeObjectURL(m.audioUrl));
    setMessages([]);
    setDocCount(0);
    setSessionKey((k) => k + 1);
  }, [messages]);

  return (
    <div className="app-bg flex h-screen overflow-hidden">
      <IconRail active={panel} onSelect={setPanel} />

      <div className="flex min-w-0 flex-1 flex-col">
        <SessionBar
          title={sessionTitle}
          live={messages.length > 0}
          onEndSession={() => void endSession()}
          canEnd={(messages.length > 0 || docCount > 0) && !busy}
        />
        {sessionError && (
          <p className="border-b border-danger/20 bg-danger/10 px-4 py-2 text-[13px] text-danger">
            {sessionError}
          </p>
        )}

        <div className="flex min-h-0 flex-1 flex-col lg:flex-row">
          {/* Left: context panel driven by the icon rail */}
          <aside className="scroll-thin shrink-0 overflow-y-auto border-b border-hairline p-4 lg:w-72 lg:border-b-0 lg:border-r">
            {panel === "tools" ? (
              <ToolsPanel />
            ) : (
              <DocumentsPanel
                key={sessionKey}
                onAudioFile={handleVoice}
                onCorpusChange={onCorpusChange}
                recorderError={recorder.error}
                busy={busy}
                sessionKey={sessionKey}
              />
            )}
          </aside>

          {/* Center: conversation */}
          <main className="flex min-h-0 min-w-0 flex-1 flex-col p-4">
            <h2 className="mb-4 text-h4">Conversation</h2>
            <div className="min-h-0 flex-1">
              <ChatWindow messages={messages} />
            </div>
            <div className="mt-4">
              <Composer
                onSend={handleText}
                onToggleRecord={recorder.toggle}
                recording={recorder.recording}
                disabled={busy}
              />
              <p className="mt-2 text-center text-[13px] text-text-low">
                Answers depend on uploaded content and may be incomplete.
              </p>
            </div>
          </main>

          {/* Right: retrieval + reasoning detail */}
          <aside className="scroll-thin shrink-0 space-y-7 overflow-y-auto border-t border-hairline p-4 lg:w-80 lg:border-l lg:border-t-0">
            <SourcesPanel sources={latest?.sources ?? []} />
            <GraphPathPanel toolPath={latest?.toolPath ?? []} />
            <MetricsPanel metrics={latest?.metrics} />
          </aside>
        </div>
      </div>
    </div>
  );
}
