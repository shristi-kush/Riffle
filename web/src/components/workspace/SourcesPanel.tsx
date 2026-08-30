import { useState } from "react";
import type { Source } from "../../types";

interface Props {
  sources: Source[];
}

const PREVIEW_COUNT = 3;

export default function SourcesPanel({ sources }: Props) {
  const [expanded, setExpanded] = useState(false);
  const visible = expanded ? sources : sources.slice(0, PREVIEW_COUNT);
  const hidden = sources.length - visible.length;

  return (
    <section>
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-h4">Retrieved Sources</h2>
        {sources.length > 0 && (
          <span className="rounded-md border border-hairline bg-white/[0.04] px-2 py-0.5 font-mono text-[11px] text-text-med">
            Top {sources.length}
          </span>
        )}
      </div>

      {sources.length === 0 ? (
        <p className="rounded-xl border border-dashed border-white/10 px-3 py-4 text-small text-text-low">
          Passages that ground the answer will appear here after you ask a question.
        </p>
      ) : (
        <>
          <ul className="space-y-2">
            {visible.map((s, i) => (
              <li
                key={`${s.title}-${i}`}
                className="surface flex items-start justify-between gap-3 rounded-xl px-3 py-2.5"
              >
                <div className="min-w-0">
                  <p className="truncate text-small font-medium text-text-high">{s.title}</p>
                  {s.location && (
                    <p className="font-mono text-[11px] text-text-low">{s.location}</p>
                  )}
                  <p className="mt-1 line-clamp-2 text-[13px] leading-snug text-text-med">
                    {s.snippet}
                  </p>
                </div>
                <span className="shrink-0 font-mono text-[11px] text-cyan-accent">
                  Score {s.score.toFixed(2)}
                </span>
              </li>
            ))}
          </ul>

          {hidden > 0 && (
            <button
              onClick={() => setExpanded(true)}
              className="mt-3 text-small font-medium text-cyan-accent transition hover:opacity-80"
            >
              View all sources ({sources.length}) &rarr;
            </button>
          )}
        </>
      )}
    </section>
  );
}
