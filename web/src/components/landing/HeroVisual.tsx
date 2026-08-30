import { DocIcon, MicIcon } from "../icons";
import Waveform from "../Waveform";

/**
 * One beat: speak a question, get an answer that points at a page.
 */
export default function HeroVisual() {
  return (
    <div className="relative mx-auto w-full max-w-md">
      <div
        className="relative overflow-hidden rounded-3xl border border-hairline bg-base-1/85 p-6 shadow-panel sm:p-7"
        aria-label="Voice question grounded in a cited page"
      >
        <div className="mb-6 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <span className="relative flex h-10 w-10 items-center justify-center">
              <span className="absolute inset-0 animate-pulse-ring rounded-full border border-cyan-accent/40" />
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-signature text-base-1">
                <MicIcon className="h-5 w-5" />
              </span>
            </span>
            <span className="text-small font-medium text-text-high">Listening...</span>
          </div>
          <span className="font-mono text-[11px] text-text-low">00:07</span>
        </div>

        <Waveform bars={36} className="h-10 w-full opacity-80" />

        <p className="mt-6 text-h4 text-text-high">
          What does the agreement say about renewal terms?
        </p>

        <div className="mt-5 rounded-2xl border border-white/[0.06] bg-white/[0.03] px-4 py-3">
          <p className="text-small leading-relaxed text-text-med">
            Clause 12.4 auto-renews for successive 12-month terms unless either party gives
            30 days written notice.
          </p>
          <span className="mt-3 inline-flex items-center gap-1.5 rounded-full border border-cyan-accent/25 bg-cyan-accent/10 px-2.5 py-1 font-mono text-[11px] text-cyan-accent">
            <DocIcon className="h-3.5 w-3.5" />
            MSA.pdf · page 4
          </span>
        </div>
      </div>

      <div className="pointer-events-none absolute -inset-8 -z-10 rounded-full bg-signature-soft blur-3xl" />
    </div>
  );
}
