import Link from "next/link";
import type { ModeBadge } from "@/lib/mode";

export function SiteHeader({
  mode,
  review = false,
}: {
  mode?: ModeBadge;
  review?: boolean;
}) {
  return (
    <header className="header">
      <div className="header-inner">
        <Link className="brand" href="/">
          LawTrace HK
        </Link>
        <nav className="nav" aria-label="Primary">
          <Link href="/">Explore</Link>
          <Link href="/collections/">Collections</Link>
          <Link href="/insights/">Insights</Link>
          <Link href="/methodology/">Methodology</Link>
          {review ? <Link href="/review/">Local review</Link> : null}
        </nav>
        {mode ? (
          <span className={`mode-badge tone-${mode.tone}`} title={mode.detail}>
            {mode.label}
          </span>
        ) : null}
      </div>
    </header>
  );
}

export function SiteFooter() {
  return (
    <footer className="footer">
      <div className="footer-inner">
        <p>
          LawTrace is a research prototype. It compares official open-data XML
          snapshots and is not a verified copy of legislation. Consult{" "}
          <a href="https://www.elegislation.gov.hk/" rel="noreferrer">
            Hong Kong e-Legislation
          </a>{" "}
          for official verified copies.
        </p>
      </div>
    </footer>
  );
}
