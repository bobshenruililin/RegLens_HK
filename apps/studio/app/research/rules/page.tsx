import Link from "next/link";
import { requireUser } from "../../../lib/auth-server";
import { listRulesIndex } from "../../../lib/research-data";

export const dynamic = "force-dynamic";

export default async function ResearchRulesPage() {
  await requireUser();
  const rules = await listRulesIndex();

  return (
    <section className="panel">
      <h1>Rules and legal tests</h1>
      <p>
        Reviewed rule and legal-test propositions from the active Studio corpus.
      </p>
      {rules.length === 0 && <p>No reviewed rule or legal-test propositions found.</p>}
      <div className="prop-list">
        {rules.map((prop) => (
          <div className="prop" key={`${prop.decision_id}-${prop.client_ref}`}>
            <div className="prop-type">
              {prop.regulator_code} · {prop.prop_type} · {prop.review_status || "none"}
            </div>
            <p className="claim">{prop.claim_text}</p>
            <p style={{ color: "var(--muted)" }}>
              {prop.title} ({prop.external_ref})
            </p>
            <Link href={`/research/compare?ids=${prop.decision_id}`}>Compare decision</Link>
            {prop.evidence.length > 0 && (
              <ul>
                {prop.evidence.map((ev, index) => (
                  <li key={index}>
                    page {ev.page_no}: "{ev.quote}"
                  </li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}
