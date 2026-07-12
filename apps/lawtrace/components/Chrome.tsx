import Link from "next/link";

export function SiteHeader({ audit = false }: { audit?: boolean }) {
  return (
    <header className="header">
      <div className="header-inner">
        <Link className="brand" href="/">
          LawTrace HK
        </Link>
        <nav className="nav" aria-label="Primary">
          <Link href="/">Home</Link>
          <Link href="/instruments/cap-614/">Cap. 614</Link>
          <Link href="/instruments/cap-599g/">Cap. 599G</Link>
          <Link href="/insights/">Insights</Link>
          <Link href="/methodology/">Methodology</Link>
          {audit ? <Link href="/audit/">Audit</Link> : null}
        </nav>
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
