import Link from "next/link";
import { listAuthoritiesIndex } from "../../lib/research-data";

export const dynamic = "force-dynamic";

export default async function AuthoritiesPage() {
  const authorities = await listAuthoritiesIndex();

  return (
    <section className="panel">
      <h1>Rules and authorities</h1>
      <p>
        Reviewed rule, legal-test, and cited-authority propositions from the
        active Studio corpus.
      </p>
      {authorities.length === 0 && <p>No reviewed rules or authorities found.</p>}
      <div className="prop-list">
        {authorities.map((prop) => (
          <div className="prop" key={`${prop.decision_id}-${prop.client_ref}`}>
            <div className="prop-type">
              {prop.regulator_code} · {prop.prop_type} · {prop.epistemic_class} ·{" "}
              {prop.review_status || "none"}
            </div>
            <p className="claim">{prop.claim_text}</p>
            <p style={{ color: "var(--muted)" }}>
              {prop.title} ({prop.external_ref})
            </p>
            <Link href={`/decisions/${prop.decision_id}`}>Open decision</Link>
            {" · "}
            <Link href={`/review/${prop.decision_id}`}>Review</Link>
            {prop.evidence.length > 0 && (
              <ul>
                {prop.evidence.map((ev, index) => (
                  <li key={index}>
                    page {ev.page_no}: “{ev.quote}”
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
