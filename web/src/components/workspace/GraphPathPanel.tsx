import { CalculatorIcon, DatabaseIcon, DocIcon, GlobeIcon } from "../icons";

interface Props {
  toolPath: string[];
}

/** Icons for the real LangGraph tool names exposed by the backend. */
const TOOL_ICONS: Record<string, typeof DocIcon> = {
  search_documents: DocIcon,
  calculator: CalculatorIcon,
  sql_metadata_query: DatabaseIcon,
  web_search: GlobeIcon,
};

export default function GraphPathPanel({ toolPath }: Props) {
  return (
    <section>
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-h4">Graph Reasoning Path</h2>
        <span className="rounded-md bg-purple-accent/15 px-2 py-0.5 font-mono text-[11px] text-purple-accent">
          LangGraph
        </span>
      </div>

      {toolPath.length === 0 ? (
        <p className="rounded-xl border border-dashed border-white/10 px-3 py-4 text-small text-text-low">
          The tools the agent calls will be traced here.
        </p>
      ) : (
        <div className="flex flex-wrap items-center gap-x-2 gap-y-2">
          {toolPath.map((tool, i) => {
            const Icon = TOOL_ICONS[tool];
            const last = i === toolPath.length - 1;
            return (
              <div key={`${tool}-${i}`} className="flex items-center gap-2">
                <span
                  className={`flex items-center gap-1.5 rounded-lg border px-2.5 py-1.5 font-mono text-[11px] ${
                    last
                      ? "border-purple-accent/40 bg-purple-accent/10 text-purple-accent"
                      : "border-hairline bg-white/[0.04] text-text-med"
                  }`}
                >
                  {Icon && <Icon className="h-3.5 w-3.5" />}
                  {tool}
                </span>
                {!last && <span className="text-text-low">&rarr;</span>}
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
