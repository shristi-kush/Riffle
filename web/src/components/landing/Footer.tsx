import { Link } from "react-router-dom";
import { ArrowRightIcon, BrandMark } from "../icons";

export default function Footer() {
  return (
    <footer className="border-t border-hairline">
      <div className="mx-auto max-w-6xl px-5 py-12 md:px-8">
        <div className="gradient-border flex flex-col items-start justify-between gap-6 rounded-2xl p-7 md:flex-row md:items-center">
          <div>
            <h3 className="text-h3">Ready to talk to your documents?</h3>
            <p className="mt-1.5 text-small text-text-med">
              Upload a PDF and ask your first question - nothing leaves your machine.
            </p>
          </div>
          <Link to="/app" className="btn-primary shrink-0">
            Open Riffle
            <ArrowRightIcon />
          </Link>
        </div>

        <div className="mt-10 flex flex-col items-center justify-between gap-4 text-small text-text-low md:flex-row">
          <div className="flex items-center gap-2">
            <BrandMark className="h-4 w-4" />
            <span>Riffle - voice-enabled agentic RAG</span>
          </div>
          <div className="flex items-center gap-6">
            <a href="/docs" className="transition hover:text-text-med">
              API docs
            </a>
            <span>Local-first. Private by default.</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
