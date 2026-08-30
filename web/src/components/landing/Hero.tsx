import { Link } from "react-router-dom";
import { ArrowRightIcon } from "../icons";
import HeroVisual from "./HeroVisual";

const TRUST = ["Runs locally", "Private by default"];

export default function Hero() {
  return (
    <section className="relative overflow-hidden">
      <div className="mx-auto grid max-w-6xl items-center gap-14 px-5 py-16 md:px-8 md:py-24 lg:grid-cols-2">
        <div>
          <span className="eyebrow inline-flex items-center gap-2 rounded-full border border-hairline bg-white/[0.04] px-3 py-1.5 text-cyan-accent">
            <span className="h-1.5 w-1.5 rounded-full bg-cyan-accent" />
            Voice AI built for real context
          </span>

          <h1 className="mt-6 text-h1">
            Voice AI with
            <br />
            <span className="gradient-text">a Retrieval Memory</span>
          </h1>

          <p className="mt-5 max-w-md text-body text-text-med">
            Grounded, context-aware conversations that pull from your own documents and
            reason with LangGraph orchestration - entirely on your machine.
          </p>

          <div className="mt-8 flex flex-wrap items-center gap-3">
            <Link to="/app" className="btn-primary">
              Open Riffle
              <ArrowRightIcon />
            </Link>
            <a href="#how-it-works" className="btn-ghost">
              How it works
            </a>
          </div>

          <div className="mt-7 flex flex-wrap items-center gap-6">
            {TRUST.map((t) => (
              <span key={t} className="flex items-center gap-2 text-small text-text-low">
                <span className="h-2 w-2 rounded-full bg-text-low/60" />
                {t}
              </span>
            ))}
          </div>
        </div>

        <HeroVisual />
      </div>
    </section>
  );
}
