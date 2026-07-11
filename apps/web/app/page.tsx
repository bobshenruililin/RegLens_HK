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
      <h1>RegLens HK</h1>
      <p>
        Milestone 2A contracts on the MVP backbone: immutable extraction runs,
        synthetic fixtures, human review, publication gate, and keyword FTS.
        Semantic search and live crawling are disabled.
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
        <Link href="/search">Search published propositions</Link>
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
          No seed found. Run{" "}
          <code>
            python -m reglens_worker ingest --manifest
            fixtures/manifests/m1.jsonl --demo-auto-approve-synthetic
          </code>{" "}
          from the repo root (with <code>PYTHONPATH=services/worker</code>).
        </p>
      )}
    </section>
  );
}
