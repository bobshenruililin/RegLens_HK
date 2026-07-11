import { getSyncStatus } from "../../lib/research-data";

export const dynamic = "force-dynamic";

export default async function SyncPage() {
  const status = await getSyncStatus();

  return (
    <section className="panel">
      <h1>Source sync</h1>
      <p>{status.message}</p>
      <p className="prop-type">Mode: {status.mode}</p>
      {status.rows.length === 0 && (
        <p className="warning">
          No live source sync rows to display. This page is a read-only status
          placeholder and does not fetch or import source documents.
        </p>
      )}
      {status.rows.length > 0 && (
        <div className="prop-list">
          {status.rows.map((row) => (
            <div className="prop" key={row.source_id}>
              <div className="prop-type">
                {row.regulator_code} · {row.visibility} · consent {row.consent_status}
              </div>
              <p className="claim">
                {row.collection_name} (<code>{row.source_id}</code>)
              </p>
              <dl className="meta-grid">
                <div>
                  <dt>Documents</dt>
                  <dd>{row.document_count}</dd>
                </div>
                <div>
                  <dt>Latest document</dt>
                  <dd>{row.latest_document_created_at ? String(row.latest_document_created_at) : "none"}</dd>
                </div>
                <div>
                  <dt>Jobs</dt>
                  <dd>
                    pending {row.pending_jobs} · running {row.running_jobs} · failed{" "}
                    {row.failed_jobs}
                  </dd>
                </div>
              </dl>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
