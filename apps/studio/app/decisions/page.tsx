import Link from "next/link";
import { listDecisions } from "../../lib/data";
import { isDemoMode, isPostgresMode } from "../../lib/mode";
import { listDecisionsPg } from "../../lib/pg-data";

export const dynamic = "force-dynamic";

export default async function DecisionsListPage() {
  if (isDemoMode()) {
    const decisions = listDecisions();
    return (
      <section className="panel">
        <h1>Decisions</h1>
        <p>Seed decisions from <code>data/seed</code>.</p>
        <div className="prop-list">
          {decisions.map((d) => (
            <div className="prop" key={d.id}>
              <div className="prop-type">
                {d.regulator_code} · {d.profession}
              </div>
              <p className="claim">{d.title}</p>
              <Link href={`/decisions/${d.id}`}>Open</Link>
              {" · "}
              <Link href={`/review/${d.id}`}>Review</Link>
            </div>
          ))}
        </div>
      </section>
    );
  }

  if (!isPostgresMode()) {
    return (
      <section className="panel">
        <h1>Decisions</h1>
        <p className="warning">Unsupported mode.</p>
      </section>
    );
  }

  const decisions = await listDecisionsPg();
  return (
    <section className="panel">
      <h1>Decisions</h1>
      <p>Studio decision aggregates (PostgreSQL).</p>
      {decisions.length === 0 && <p>No decisions.</p>}
      <div className="prop-list">
        {decisions.map((d) => (
          <div className="prop" key={d.id}>
            <div className="prop-type">
              {d.regulator_code} · {d.profession} · {d.fixture_kind}
            </div>
            <p className="claim">{d.title || d.external_ref}</p>
            <Link href={`/decisions/${d.id}`}>Open</Link>
            {" · "}
            <Link href={`/review/${d.id}`}>Review</Link>
          </div>
        ))}
      </div>
    </section>
  );
}
