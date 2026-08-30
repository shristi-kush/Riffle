interface Props {
  bars?: number;
  className?: string;
  animated?: boolean;
}

/**
 * Decorative audio waveform. Bar heights follow a fixed pseudo-random pattern
 * so the shape is stable across renders (no layout jitter).
 */
export default function Waveform({ bars = 28, className = "", animated = true }: Props) {
  const heights = Array.from({ length: bars }, (_, i) => {
    const wave = Math.sin((i / bars) * Math.PI);
    const jitter = ((i * 37) % 11) / 22;
    return Math.max(0.18, Math.min(1, wave * 0.85 + jitter));
  });

  return (
    <div className={`flex items-center gap-[3px] ${className}`} aria-hidden="true">
      {heights.map((h, i) => (
        <span
          key={i}
          className={`w-[2px] rounded-full bg-gradient-to-t from-cyan-accent/30 via-primary-400/70 to-purple-accent/60 ${
            animated ? "animate-wave-bar" : ""
          }`}
          style={{
            height: `${Math.round(h * 100)}%`,
            animationDelay: `${(i % 9) * 90}ms`,
          }}
        />
      ))}
    </div>
  );
}
