import type { ChatMessage } from "../types";
import { SparkIcon, UserIcon } from "./icons";
import TypingIndicator from "./TypingIndicator";

export default function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";

  return (
    <article className="animate-fade-up">
      <div className="mb-1.5 flex items-center gap-2 text-[11px]">
        {isUser ? (
          <>
            <UserIcon className="h-3.5 w-3.5 text-text-low" />
            <span className="font-medium text-text-med">User</span>
          </>
        ) : (
          <>
            <SparkIcon className="h-3.5 w-3.5 text-cyan-accent" />
            <span className="font-medium text-cyan-accent">Assistant</span>
          </>
        )}
        <span className="ml-auto font-mono text-text-low">{message.at}</span>
      </div>

      {message.transcript && (
        <p className="mb-1.5 font-mono text-[11px] italic text-text-low">
          Heard: "{message.transcript}"
        </p>
      )}

      {message.pending ? (
        <TypingIndicator />
      ) : (
        <p
          className={`whitespace-pre-wrap break-words text-body ${
            message.failed ? "text-danger" : "text-text-high"
          }`}
        >
          {message.content}
        </p>
      )}

      {message.audioUrl && (
        <audio controls autoPlay src={message.audioUrl} className="mt-3 h-9 w-64 max-w-full" />
      )}
    </article>
  );
}
