import { useEffect, useState } from "react";
import { checkHealth } from "../lib/api";

type Status = "checking" | "online" | "offline";

const CONFIG: Record<Status, { label: string; dot: string; text: string }> = {
  checking: { label: "Connecting", dot: "bg-amber-400", text: "text-amber-400" },
  online: { label: "API connected", dot: "bg-success", text: "text-success" },
  offline: { label: "API offline", dot: "bg-danger", text: "text-danger" },
};

export default function HealthBadge() {
  const [status, setStatus] = useState<Status>("checking");

  useEffect(() => {
    let active = true;
    const controller = new AbortController();

    const ping = async () => {
      const ok = await checkHealth(controller.signal);
      if (active) setStatus(ok ? "online" : "offline");
    };

    void ping();
    const timer = setInterval(() => void ping(), 15000);

    return () => {
      active = false;
      controller.abort();
      clearInterval(timer);
    };
  }, []);

  const { label, dot, text } = CONFIG[status];

  return (
    <span
      className={`hidden items-center gap-2 font-mono text-[11px] sm:inline-flex ${text}`}
      title={label}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${dot}`} />
      {label}
    </span>
  );
}
