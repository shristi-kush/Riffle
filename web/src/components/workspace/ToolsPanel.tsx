import { CalculatorIcon, DatabaseIcon, DocIcon, GlobeIcon, GraphIcon } from "../icons";

const TOOLS = [
  {
    icon: DocIcon,
    name: "search_documents",
    body: "Hybrid BM25 + dense retrieval over your PDF, then cross-encoder reranking.",
  },
  {
    icon: CalculatorIcon,
    name: "calculator",
    body: "Arithmetic the agent calls instead of doing math in its head.",
  },
  {
    icon: DatabaseIcon,
    name: "sql_metadata_query",
    body: "Read-only SQL over which documents were ingested, and when.",
  },
  {
    icon: GlobeIcon,
    name: "web_search",
    body: "Public-web fallback. Only registered when TAVILY_API_KEY is set.",
    optional: true,
  },
];

export default function ToolsPanel() {
  return (
    <section>
      <h2 className="mb-3 flex items-center gap-2 text-h4">
        <GraphIcon className="h-4 w-4 text-purple-accent" />
        Agent tools
      </h2>
      <p className="mb-4 text-[13px] text-text-med">
        The LangGraph agent picks among these each turn. The path it actually took is
        traced in the panel on the right.
      </p>

      <ul className="space-y-2">
        {TOOLS.map(({ icon: Icon, name, body, optional }) => (
          <li key={name} className="surface rounded-xl px-3 py-2.5">
            <div className="flex items-center gap-2">
              <Icon className="h-4 w-4 text-text-med" />
              <span className="font-mono text-[12px] text-text-high">{name}</span>
              {optional && (
                <span className="ml-auto rounded-md border border-hairline px-1.5 py-0.5 font-mono text-[10px] text-text-low">
                  optional
                </span>
              )}
            </div>
            <p className="mt-1.5 text-[13px] leading-snug text-text-med">{body}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}
