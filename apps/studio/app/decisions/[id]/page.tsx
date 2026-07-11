import Link from "next/link";
import { DecisionView } from "../../../components/DecisionView";
import { loadDecision } from "../../../lib/data";
import { isDemoMode, isPostgresMode } from "../../../lib/mode";
import { getDecisionReviewBundle } from "../../../lib/pg-data";

export const dynamic = "force-dynamic";

export default async function DecisionPage({
  params,
}: {
  params: { id: string };
}) {
  if (isDemoMode()) {
    const decision = loadDecision(params.id);
    if (!decision) {
      return (
        <section className="panel">
          <h1>Decision not found</h1>
          <p>
            No seed for <code>{params.id}</code>.
          </p>
        </section>
      );
    }
    return <DecisionView decision={decision} />;
  }

  if (!isPostgresMode()) {
    return (
      <section className="panel">
        <h1>Decision</h1>
        <p className="warning">Unsupported mode.</p>
      </section>
    );
  }

  const bundle = await getDecisionReviewBundle(params.id);
  if (!bundle) {
    return (
      <section className="panel">
        <h1>Decision not found</h1>
      </section>
    );
  }

  return (
    <article>
      <section className="panel">
        <div className="badge">{bundle.decision.regulator_code}</div>
        <div className="badge">{bundle.decision.profession}</div>
        <h1 className="brand" style={{ fontSize: "2rem", marginTop: "0.6rem" }}>
          {bundle.decision.title || bundle.decision.external_ref}
        </h1>
        <dl className="meta-grid">
          <div>
            <dt>External ref</dt>
            <dd>{bundle.decision.external_ref}</dd>
          </div>
          <div>
            <dt>Practitioner (as published)</dt>
            <dd>{bundle.decision.defendant_name_as_published || "—"}</dd>
          </div>
        </dl>
        <p>
          <Link href={`/review/${bundle.decision.id}`}>Open review layout</Link>
        </p>
      </section>
      <section className="panel" style={{ marginTop: "1rem" }}>
        <h2>Head revisions</h2>
        <div className="prop-list">
          {bundle.propositions.map((p) => (
            <div className="prop" key={p.revision_id}>
              <div className="prop-type">
                {p.prop_type} · {p.epistemic_class} ·{" "}
                {p.latest_review_status || "none"}
              </div>
              <p className="claim">{p.claim_text}</p>
            </div>
          ))}
        </div>
      </section>
    </article>
  );
}
