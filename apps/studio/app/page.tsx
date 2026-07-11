import Link from "next/link";
import { listDecisions, loadDecision } from "../lib/data";

export default function HomePage() {
  const decision = loadDecision();
  const decisions = listDecisions();
  const pending = decisions.reduce(
    (n, d) =>
      n +
      d.propositions.filter(
        (p) => !p.published && p.review_status !== "rejected"
      ).length,
    0
  );
  const published = decisions.reduce(
    (n, d) => n + d.propositions.filter((p) => p.published).length,
    0
  );

  return (
    <section className="panel">
      <p className="warning">
        RegLens Studio — experimental internal tool. Not deployed to GitHub
        Pages. Reads and writes <code>data/seed</code> only.
      </p>
      <h1>RegLens Studio</h1>
      <p>
        Internal ingest review workspace. Public research output ships from
        RegLens Observatory via a privacy-checked publication release.
      </p>
      <dl className="meta-grid">
        <div>
          <dt>Decisions</dt>
          <dd>{decisions.length}</dd>
        </div>
        <div>
          <dt>Published propositions</dt>
          <dd>{published}</dd>
        </div>
        <div>
          <dt>Review queue</dt>
          <dd>{pending}</dd>
        </div>
      </dl>
      <p>
        <Link href="/search">Keyword search (local seed)</Link>
        {" · "}
        <Link href="/review">Open review queue</Link>
      </p>
      {decision ? (
        <p>
          <Link href={`/decisions/${decision.id}`}>
            Open {decision.title || decision.case_ref || decision.id}
          </Link>
        </p>
      ) : (
        <p className="warning">
          Empty state: no generated seed under <code>data/seed</code>. Run{" "}
          <code>make demo-ingest</code> from the repo root.
        </p>
      )}
    </section>
  );
}
