import Link from "next/link";
import { requireUser } from "../../../lib/auth-server";
import { listCitedAuthoritiesIndex } from "../../../lib/research-data";

export const dynamic = "force-dynamic";

export default async function ResearchAuthoritiesPage() {
  await requireUser();
  const authorities = await listCitedAuthoritiesIndex();

  return (
    <section className="panel">
      <h1>Cited authorities</h1>
      <p>
        Reviewed cited-authority propositions. Synthetic demo fixtures may have
        zero or sparse cited authorities.
      </p>
      {authorities.length === 0 && (
        <p className="warning">
          No reviewed authority propositions are present in the current demo data.
        </p>
      )}
      <div className="prop-list">
        {authorities.map((prop) => (
          <div className="prop" key={`${prop.decision_id}-${prop.client_ref}`}>
            <div className="prop-type">
              {prop.regulator_code} · {prop.review_status || "none"}
            </div>
            <p className="claim">{prop.claim_text}</p>
            <p style={{ color: "var(--muted)" }}>
              {prop.title} ({prop.external_ref})
            </p>
            <Link href={`/research/compare?ids=${prop.decision_id}`}>Compare decision</Link>
          </div>
        ))}
      </div>
    </section>
  );
}
