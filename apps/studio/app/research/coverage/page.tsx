import Link from "next/link";
import { requireUser } from "../../../lib/auth-server";
import { getCoverageRows } from "../../../lib/research-data";

export const dynamic = "force-dynamic";

export default async function ResearchCoveragePage() {
  await requireUser();
  const rows = await getCoverageRows();

  return (
    <section className="panel">
      <h1>Coverage</h1>
      <p>
        Completeness view for reviewed synthetic/demo decisions. Missing surfaces
        indicate absent reviewed propositions, not absence in the primary source.
      </p>
      {rows.length === 0 && <p>No reviewed decisions are available.</p>}
      <div className="prop-list">
        {rows.map((row) => (
          <div className="prop" key={row.external_ref}>
            <div className="prop-type">
              {row.regulator_code} · {row.external_ref} · {row.reviewed_prop_count} reviewed props
            </div>
            <p className="claim">{row.title || row.external_ref}</p>
            <dl className="meta-grid">
              <div>
                <dt>Issues</dt>
                <dd>{row.issue_categories.join(", ") || "none"}</dd>
              </div>
              <div>
                <dt>Findings</dt>
                <dd>{row.finding_outcomes.join(", ") || "none"}</dd>
              </div>
              <div>
                <dt>Sanctions</dt>
                <dd>{row.sanction_categories.join(", ") || "none"}</dd>
              </div>
              <div>
                <dt>Missing core surfaces</dt>
                <dd>{row.missing_surfaces.join(", ") || "none"}</dd>
              </div>
            </dl>
            {row.id && <Link href={`/research/compare?ids=${row.id}`}>Compare</Link>}
          </div>
        ))}
      </div>
    </section>
  );
}
