import type { Metrics } from "../../types";

interface Props {
  metrics?: Metrics;
}

function Row({ label, value, tone }: { label: string; value: string; tone?: string }) {
  return (
    <div className="flex items-center justify-between py-1.5 text-small">
      <span className="text-text-med">{label}</span>
      <span className={`font-mono text-[13px] ${tone ?? "text-text-high"}`}>{value}</span>
    </div>
  );
}

export default function MetricsPanel({ metrics }: Props) {
  if (!metrics) {
    return (
      <section>
        <h2 className="mb-3 text-h4">Response Status</h2>
        <p className="rounded-xl border border-dashed border-white/10 px-3 py-4 text-small text-text-low">
          Grounding, confidence, and latency are reported after each answer.
        </p>
      </section>
    );
  }

  const confidenceTone =
    metrics.confidence === "High"
      ? "text-success"
      : metrics.confidence === "Low"
        ? "text-danger"
        : "text-text-high";

  return (
    <section>
      <h2 className="mb-2 text-h4">Response Status</h2>
      <div className="divide-y divide-white/[0.05]">
        <Row
          label="Grounding"
          value={metrics.grounded ? "Grounded" : "Ungrounded"}
          tone={metrics.grounded ? "text-success" : "text-danger"}
        />
        <Row label="Sources used" value={String(metrics.sourcesUsed)} />
        <Row label="Confidence" value={metrics.confidence} tone={confidenceTone} />
        <Row label="Latency" value={`${metrics.latencyS.toFixed(2)}s`} />
      </div>
    </section>
  );
}
