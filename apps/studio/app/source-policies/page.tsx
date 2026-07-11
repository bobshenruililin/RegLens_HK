import { isPostgresMode } from "../../lib/mode";
import { listSourcePoliciesFromDb } from "../../lib/pg-data";
import { loadSourcePoliciesFromFile } from "../../lib/policies";

export const dynamic = "force-dynamic";

export default async function SourcePoliciesPage() {
  if (isPostgresMode()) {
    try {
      const rows = await listSourcePoliciesFromDb();
      return (
        <section className="panel">
          <h1>Source policies</h1>
          <p>Read-only from <code>source_collections</code>.</p>
          <div className="prop-list">
            {rows.map((p) => (
              <div className="prop" key={p.source_id}>
                <div className="prop-type">
                  {p.regulator_code} · {p.visibility} · consent{" "}
                  {p.consent_status}
                </div>
                <p className="claim">
                  {p.collection_name} (<code>{p.source_id}</code>)
                </p>
                <p style={{ color: "var(--muted)" }}>
                  max excerpt {p.max_excerpt_chars} · attribution{" "}
                  {p.attribution_required ? "required" : "optional"}
                </p>
                {p.notes && <p>{p.notes}</p>}
              </div>
            ))}
          </div>
        </section>
      );
    } catch (err) {
      const message = err instanceof Error ? err.message : "DB error";
      return (
        <section className="panel">
          <h1>Source policies</h1>
          <p className="warning">{message}</p>
        </section>
      );
    }
  }

  const file = loadSourcePoliciesFromFile();
  return (
    <section className="panel">
      <h1>Source policies</h1>
      <p>
        Read-only from{" "}
        <code>publications/policies/source_publication_policy.v1.json</code>.
      </p>
      {!file && <p className="warning">Policy file not found.</p>}
      <div className="prop-list">
        {(file?.policies || []).map((p) => (
          <div className="prop" key={p.source_id}>
            <div className="prop-type">
              {p.regulator_code} · {p.visibility}
            </div>
            <p className="claim">
              <code>{p.source_id}</code>
            </p>
            <p style={{ color: "var(--muted)" }}>
              max excerpt {p.max_excerpt_chars} · attribution{" "}
              {p.attribution_required ? "required" : "optional"}
            </p>
            {p.notes && <p>{p.notes}</p>}
          </div>
        ))}
      </div>
    </section>
  );
}
