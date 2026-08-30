import { Link } from "react-router-dom";
import { BrandMark, ChatIcon, CodeIcon, DatabaseIcon, GraphIcon, SettingsIcon } from "../icons";

export type RailPanel = "chat" | "documents" | "tools";

interface Props {
  active: RailPanel;
  onSelect: (panel: RailPanel) => void;
}

const ITEMS: { id: RailPanel; label: string; icon: typeof ChatIcon }[] = [
  { id: "chat", label: "Conversation", icon: ChatIcon },
  { id: "documents", label: "Documents", icon: DatabaseIcon },
  { id: "tools", label: "Agent tools", icon: GraphIcon },
];

function RailButton({
  label,
  active,
  onClick,
  children,
}: {
  label: string;
  active?: boolean;
  onClick?: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      title={label}
      aria-label={label}
      aria-current={active ? "page" : undefined}
      className={`group relative flex h-10 w-10 items-center justify-center rounded-xl transition ${
        active
          ? "bg-cyan-accent/15 text-cyan-accent"
          : "text-text-low hover:bg-white/[0.06] hover:text-text-high"
      }`}
    >
      {active && (
        <span className="absolute -left-2 top-1/2 h-5 w-[2px] -translate-y-1/2 rounded-full bg-cyan-accent" />
      )}
      {children}
    </button>
  );
}

export default function IconRail({ active, onSelect }: Props) {
  return (
    <nav className="flex h-full w-14 shrink-0 flex-col items-center gap-2 border-r border-hairline bg-base-1/60 py-4">
      <Link
        to="/"
        title="Back to home"
        aria-label="Back to home"
        className="mb-3 flex h-9 w-9 items-center justify-center rounded-xl bg-signature text-base-1"
      >
        <BrandMark className="h-5 w-5" />
      </Link>

      {ITEMS.map(({ id, label, icon: Icon }) => (
        <RailButton key={id} label={label} active={active === id} onClick={() => onSelect(id)}>
          <Icon className="h-5 w-5" />
        </RailButton>
      ))}

      <a
        href="/docs"
        target="_blank"
        rel="noreferrer"
        title="API docs"
        aria-label="API docs"
        className="flex h-10 w-10 items-center justify-center rounded-xl text-text-low transition hover:bg-white/[0.06] hover:text-text-high"
      >
        <CodeIcon className="h-5 w-5" />
      </a>

      <div className="mt-auto">
        <RailButton label="Settings (coming soon)">
          <SettingsIcon className="h-5 w-5" />
        </RailButton>
      </div>
    </nav>
  );
}
