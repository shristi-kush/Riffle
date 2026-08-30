import { Link } from "react-router-dom";
import { ArrowRightIcon, BookIcon, CodeIcon, HeadsetIcon } from "../icons";

const CARDS = [
  {
    icon: CodeIcon,
    title: "Developer Tools",
    body: "Query specs, APIs, and runbooks by voice while you keep your hands on the keyboard.",
    cta: "Explore for Developers",
  },
  {
    icon: HeadsetIcon,
    title: "Support Agents",
    body: "Resolve tickets faster with accurate, cited answers pulled straight from policy docs.",
    cta: "Explore for Support",
  },
  {
    icon: BookIcon,
    title: "Research & Knowledge",
    body: "Search, synthesize, and reason across long reports and papers without losing context.",
    cta: "Explore for Research",
  },
];

export default function FeatureCards() {
  return (
    <section id="use-cases" className="mx-auto max-w-6xl px-5 pb-20 md:px-8 md:pb-28">
      <span className="eyebrow text-text-low">Built for people who rely on knowledge</span>

      <div className="mt-8 grid gap-5 md:grid-cols-3">
        {CARDS.map(({ icon: Icon, title, body, cta }) => (
          <article
            key={title}
            className="surface group rounded-2xl p-6 transition hover:border-white/15 hover:bg-base-3"
          >
            <span className="flex h-10 w-10 items-center justify-center rounded-xl border border-hairline bg-white/[0.04] text-cyan-accent">
              <Icon className="h-5 w-5" />
            </span>
            <h3 className="mt-4 text-h4">{title}</h3>
            <p className="mt-2 text-small text-text-med">{body}</p>
            <Link
              to="/app"
              className="mt-5 inline-flex items-center gap-1.5 text-small font-medium text-cyan-accent transition group-hover:gap-2.5"
            >
              {cta}
              <ArrowRightIcon />
            </Link>
          </article>
        ))}
      </div>
    </section>
  );
}
