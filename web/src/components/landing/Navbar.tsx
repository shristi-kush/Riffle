import { Link } from "react-router-dom";
import { BrandMark } from "../icons";

export default function Navbar() {
  return (
    <header className="sticky top-0 z-30 border-b border-hairline bg-base-1/80 backdrop-blur-xl">
      <nav className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4 md:px-8">
        <Link to="/" className="flex items-center gap-2.5">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-signature text-base-1">
            <BrandMark className="h-5 w-5" />
          </span>
          <span className="text-h4 font-semibold tracking-tight">Riffle</span>
        </Link>

        <div className="hidden items-center gap-8 md:flex">
          <a href="#how-it-works" className="text-small text-text-med transition hover:text-text-high">
            How it works
          </a>
          <a href="#use-cases" className="text-small text-text-med transition hover:text-text-high">
            Use cases
          </a>
        </div>

        <Link to="/app" className="btn-primary">
          Open Riffle
        </Link>
      </nav>
    </header>
  );
}
