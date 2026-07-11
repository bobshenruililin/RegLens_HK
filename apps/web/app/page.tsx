import Link from "next/link";
import { loadDecision } from "../lib/decision";

export default function HomePage() {
  const decision = loadDecision();
  return (
    <section className="panel">
      <h1>Milestone 1 demo</h1>
      <p>
        Fixture ingest produces a source-linked decision seed. Open the decision
        detail page to inspect each proposition against its page span.
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
          </code>{" "}
          from the repo root (with <code>PYTHONPATH=services/worker</code>).
        </p>
      )}
    </section>
  );
}
