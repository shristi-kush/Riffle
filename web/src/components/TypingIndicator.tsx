export default function TypingIndicator() {
  return (
    <div className="flex items-center gap-2 text-small italic text-text-med" role="status">
      <span className="flex items-center gap-1">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="h-1.5 w-1.5 animate-blink rounded-full bg-cyan-accent"
            style={{ animationDelay: `${i * 200}ms` }}
          />
        ))}
      </span>
      Retrieving context...
    </div>
  );
}
