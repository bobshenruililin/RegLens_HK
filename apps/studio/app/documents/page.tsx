import Link from "next/link";
import { listDecisions } from "../../lib/data";
import { isDemoMode, isPostgresMode } from "../../lib/mode";
import { listDocuments } from "../../lib/pg-data";

export const dynamic = "force-dynamic";

export default async function DocumentsPage() {
  if (isDemoMode()) {
    const decisions = listDecisions();
    return (
      <section className="panel">
        <h1>Documents</h1>
        <p>
          Demo mode: documents are implied by seed decisions under{" "}
          <code>data/seed</code>.
        </p>
        <div className="prop-list">
          {decisions.map((d) => (
            <div className="prop" key={d.id}>
              <div className="prop-type">
                {d.regulator_code} · {d.document_id}
              </div>
              <p className="claim">{d.title}</p>
              <Link href={`/documents/${d.document_id}`}>Open</Link>
              {" · "}
              <Link href={`/decisions/${d.id}`}>Decision</Link>
            </div>
          ))}
        </div>
      </section>
    );
  }

  if (!isPostgresMode()) {
    return (
      <section className="panel">
        <h1>Documents</h1>
        <p className="warning">Unsupported mode.</p>
      </section>
    );
  }

  const docs = await listDocuments();
  return (
    <section className="panel">
      <h1>Documents</h1>
      <p>Logical documents from PostgreSQL.</p>
      {docs.length === 0 && <p>No documents.</p>}
      <div className="prop-list">
        {docs.map((d) => (
          <div className="prop" key={d.id}>
            <div className="prop-type">
              {d.regulator_code} · {d.source_id} · {d.ingest_status}
            </div>
            <p className="claim">{d.title || d.external_ref}</p>
            <Link href={`/documents/${d.id}`}>Open</Link>
          </div>
        ))}
      </div>
    </section>
  );
}
