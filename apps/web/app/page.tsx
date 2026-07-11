import Link from "next/link";
import { loadDecision } from "../lib/decision";

export default function HomePage() {
  const decision = loadDecision();
  return (
    <section className="panel">
      <h1>Milestone 2A demo</h1>
      <p>
        Synthetic fixture ingest produces an immutable run artifact and a demo
        pointer. Open the decision detail page to inspect propositions against
        source spans. Default ingest is pending/unpublished.
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
            python -m reglens_worker ingest --manifest fixtures/manifests/m1.jsonl
            --demo-auto-approve-synthetic
          </code>{" "}
          from the repo root (with <code>PYTHONPATH=services/worker</code>).
        </p>
      )}
    </section>
  );
}
