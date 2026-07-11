import Link from "next/link";
import { requireUser } from "../../../lib/auth-server";
import { listSanctionIndex } from "../../../lib/research-data";

export const dynamic = "force-dynamic";

export default async function ResearchSanctionsPage() {
  await requireUser();
  const sanctions = await listSanctionIndex();

  return (
    <section className="panel">
      <h1>Research sanctions</h1>
      <p>
        Normalized sanction categories from reviewed synthetic/demo annotations,
        with matching sanction and costs propositions where available.
      </p>
      <div className="prop-list">
        {sanctions.map((sanction) => (
          <div className="prop" key={sanction.code}>
            <div className="prop-type">
              {sanction.code} · {sanction.decision_count} decision
              {sanction.decision_count === 1 ? "" : "s"}
            </div>
            <p className="claim">{sanction.label}</p>
            {sanction.decisions.length === 0 ? (
              <p>No reviewed decisions.</p>
            ) : (
              <ul>
                {sanction.decisions.map((decision) => (
                  <li key={decision.external_ref}>
                    {decision.title || decision.external_ref}{" "}
                    <span className="badge">{decision.regulator_code}</span>
                    {decision.decision_id && (
                      <Link href={`/research/compare?ids=${decision.decision_id}`}>
                        Compare
                      </Link>
                    )}
                  </li>
                ))}
              </ul>
            )}
            {sanction.propositions.length > 0 && (
              <details>
                <summary>Reviewed sanction/cost propositions</summary>
                <ul>
                  {sanction.propositions.map((prop) => (
                    <li key={`${prop.decision_id}-${prop.client_ref}`}>
                      <span className="badge">{prop.prop_type}</span>
                      {prop.claim_text}
                    </li>
                  ))}
                </ul>
              </details>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}
