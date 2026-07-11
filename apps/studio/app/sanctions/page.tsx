import Link from "next/link";
import { listSanctionIndex } from "../../lib/research-data";

export const dynamic = "force-dynamic";

export default async function SanctionsPage() {
  const sanctions = await listSanctionIndex();

  return (
    <section className="panel">
      <h1>Sanctions</h1>
      <p>
        Normalized sanction categories from reviewed annotations, with matching
        sanction/cost proposition text where available.
      </p>
      <div className="prop-list">
        {sanctions.map((sanction) => (
          <div className="prop" key={sanction.code}>
            <div className="prop-type">
              {sanction.code} · {sanction.decision_count} decision
              {sanction.decision_count === 1 ? "" : "s"}
            </div>
            <p className="claim">{sanction.label}</p>
            {sanction.decisions.length === 0 && <p>No reviewed decisions.</p>}
            {sanction.decisions.length > 0 && (
              <ul>
                {sanction.decisions.map((decision) => (
                  <li key={decision.external_ref}>
                    {decision.decision_id ? (
                      <Link href={`/decisions/${decision.decision_id}`}>
                        {decision.title || decision.external_ref}
                      </Link>
                    ) : (
                      decision.title || decision.external_ref
                    )}{" "}
                    <span className="badge">{decision.regulator_code}</span>
                  </li>
                ))}
              </ul>
            )}
            {sanction.propositions.length > 0 && (
              <details>
                <summary>Reviewed sanction propositions</summary>
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
