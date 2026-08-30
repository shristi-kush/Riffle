import { useEffect, useRef } from "react";
import type { ChatMessage } from "../types";
import MessageBubble from "./MessageBubble";
import { SparkIcon } from "./icons";

function EmptyState() {
  return (
    <div className="flex h-full flex-col items-center justify-center px-6 text-center">
      <span className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-signature text-base-1 shadow-glow">
        <SparkIcon className="h-7 w-7" />
      </span>
      <h2 className="text-h3">Ask anything about your documents</h2>
      <p className="mt-2 max-w-sm text-small text-text-med">
        Upload a PDF from the Documents panel, then ask by text or voice. Retrieved
        sources and the agent's reasoning path show up as you go.
      </p>
    </div>
  );
}

export default function ChatWindow({ messages }: { messages: ChatMessage[] }) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  if (messages.length === 0) return <EmptyState />;

  return (
    <div className="scroll-thin h-full space-y-6 overflow-y-auto pr-2">
      {messages.map((m) => (
        <MessageBubble key={m.id} message={m} />
      ))}
      <div ref={endRef} />
    </div>
  );
}
