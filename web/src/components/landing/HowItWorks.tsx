import { CheckCircleIcon, DatabaseIcon, GraphIcon, MicIcon } from "../icons";
import Waveform from "../Waveform";

const STEPS = [
  {
    icon: MicIcon,
    title: "Voice Input",
    body: "Capture natural speech, transcribed locally with faster-whisper.",
  },
  {
    icon: DatabaseIcon,
    title: "Retrieval (RAG)",
    body: "Hybrid BM25 + dense search, then cross-encoder reranking.",
  },
  {
    icon: GraphIcon,
    title: "Graph Orchestration",
    body: "A LangGraph agent routes across your documents and tools.",
  },
  {
    icon: CheckCircleIcon,
    title: "Grounded Answer",
    body: "Cited, low-hallucination responses - spoken back with Piper.",
    accent: true,
  },
];

export default function HowItWorks() {
  return (
    <section id="how-it-works" className="mx-auto max-w-6xl px-5 py-16 md:px-8 md:py-24">
      <span className="eyebrow text-cyan-accent">How it works</span>
      <h2 className="mt-3 text-h2">From voice to grounded answer</h2>

      <div className="mt-14 grid gap-10 md:grid-cols-2 lg:grid-cols-4">
        {STEPS.map(({ icon: Icon, title, body, accent }, i) => (
          <div key={title} className="relative flex flex-col items-center text-center">
            {/* Connector waveform (between steps, desktop only) */}
            {i < STEPS.length - 1 && (
              <Waveform
                bars={18}
                className="absolute left-[calc(50%+2.75rem)] top-8 hidden h-8 w-[calc(100%-5.5rem)] opacity-45 lg:flex"
              />
            )}

            <div className="relative">
              {accent && (
                <span className="absolute inset-0 animate-pulse-ring rounded-full border border-purple-accent/40" />
              )}
              <span
                className={`flex h-16 w-16 items-center justify-center rounded-full border ${
                  accent
                    ? "border-purple-accent/40 bg-purple-accent/15 text-purple-accent shadow-glow"
                    : "border-hairline bg-base-2 text-text-high"
                }`}
              >
                <Icon className="h-6 w-6" />
              </span>
            </div>

            <h3 className="mt-5 text-h4">
              {i + 1}. {title}
            </h3>
            <p className="mt-2 max-w-[15rem] text-small text-text-med">{body}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
