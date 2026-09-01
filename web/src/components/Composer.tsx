import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import { MicIcon, SendIcon } from "./icons";

interface Props {
  onSend: (text: string) => void;
  onToggleRecord: () => void;
  recording: boolean;
  disabled?: boolean;
}

export default function Composer({ onSend, onToggleRecord, recording, disabled }: Props) {
  const [text, setText] = useState("");
  const ref = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  }, [text]);

  const submit = () => {
    const value = text.trim();
    if (!value || disabled) return;
    onSend(value);
    setText("");
  };

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <div className="surface flex items-end gap-2 rounded-2xl px-3 py-2">
      <button
        onClick={onToggleRecord}
        disabled={disabled && !recording}
        aria-label={recording ? "Stop recording and send" : "Record a voice question"}
        title={recording ? "Stop recording and send" : "Record a voice question"}
        className={`mb-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg transition ${
          recording
            ? "animate-pulse bg-danger/90 text-white"
            : "text-text-low hover:bg-white/[0.06] hover:text-text-high"
        } disabled:cursor-not-allowed disabled:opacity-40`}
      >
        <MicIcon className="h-4 w-4" />
      </button>

      <textarea
        ref={ref}
        rows={1}
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={onKeyDown}
        placeholder={recording ? "Recording... click the mic to send" : "Ask a follow-up..."}
        disabled={recording}
        className="scroll-thin max-h-40 flex-1 resize-none bg-transparent py-2 text-body text-text-high placeholder:text-text-low focus:outline-none disabled:opacity-60"
      />

      <button
        onClick={submit}
        disabled={disabled || !text.trim()}
        aria-label="Send message"
        className="mb-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-signature text-base-1 transition enabled:hover:shadow-glow-cyan disabled:cursor-not-allowed disabled:opacity-30"
      >
        <SendIcon className="h-4 w-4" />
      </button>
    </div>
  );
}
