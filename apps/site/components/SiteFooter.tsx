import Link from "next/link";

export function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="site-footer__inner">
        <p>
          <strong>RegLens Observatory</strong> is a read-only research surface for
          structured disciplinary materials. It is not legal advice.
        </p>
        <p>
          Search is keyword and structured-field matching only — not full-text
          search engines or semantic retrieval.{" "}
          <Link href="/methodology/">Methodology</Link>
          {" · "}
          <Link href="/data/">Release data</Link>
        </p>
      </div>
    </footer>
  );
}
