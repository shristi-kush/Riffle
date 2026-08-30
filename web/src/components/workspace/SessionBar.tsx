import HealthBadge from "../HealthBadge";

interface Props {
  title: string;
  live: boolean;
  onEndSession: () => void;
  canEnd: boolean;
}

export default function SessionBar({ title, live, onEndSession, canEnd }: Props) {
  return (
    <header className="flex items-center justify-between gap-4 border-b border-hairline bg-base-1/60 px-4 py-3">
      <div className="flex min-w-0 items-center gap-3 font-mono text-small">
        <span className="shrink-0 text-text-low">Session:</span>
        <span className="truncate text-text-high">{title}</span>
        {live && (
          <span className="flex shrink-0 items-center gap-1.5 text-success">
            <span className="h-1.5 w-1.5 rounded-full bg-success" />
            Live
          </span>
        )}
      </div>

      <div className="flex shrink-0 items-center gap-3">
        <HealthBadge />
        <button
          onClick={onEndSession}
          disabled={!canEnd}
          className="rounded-lg border border-white/10 bg-white/[0.03] px-3 py-1.5 text-small text-text-med transition hover:border-white/20 hover:text-text-high disabled:cursor-not-allowed disabled:opacity-40"
        >
          End Session
        </button>
      </div>
    </header>
  );
}
