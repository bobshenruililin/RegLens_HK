import Link from "next/link";
import { listDecisions, loadDecision } from "../../../lib/data";
import { isDemoMode, isPostgresMode } from "../../../lib/mode";
import { getDocument } from "../../../lib/pg-data";

export const dynamic = "force-dynamic";

export default async function DocumentDetailPage({
  params,
}: {
  params: { id: string };
}) {
  if (isDemoMode()) {
    const decisions = listDecisions().filter(
      (d) => d.document_id === params.id || d.id === params.id
    );
    const decision =
      decisions[0] ||
      loadDecision(params.id) ||
      listDecisions().find((d) => d.document_sha256?.startsWith(params.id));
    if (!decision) {
      return (
        <section className="panel">
          <h1>Document not found</h1>
          <p>
            No seed document for <code>{params.id}</code>.
          </p>
        </section>
      );
    }
    return (
      <section className="panel">
        <h1>{decision.title}</h1>
        <dl className="meta-grid">
          <div>
            <dt>Document id</dt>
            <dd>{decision.document_id}</dd>
          </div>
          <div>
            <dt>SHA-256</dt>
            <dd>
              <code>{decision.document_sha256.slice(0, 16)}…</code>
            </dd>
          </div>
          <div>
            <dt>Pages</dt>
            <dd>{decision.pages.length}</dd>
          </div>
        </dl>
        <p>
          <Link href={`/decisions/${decision.id}`}>Open decision</Link>
          {" · "}
          <Link href={`/review/${decision.id}`}>Review</Link>
        </p>
      </section>
    );
  }

  if (!isPostgresMode()) {
    return (
      <section className="panel">
        <h1>Document</h1>
        <p className="warning">Unsupported mode.</p>
      </section>
    );
  }

  const doc = await getDocument(params.id);
  if (!doc) {
    return (
      <section className="panel">
        <h1>Document not found</h1>
      </section>
    );
  }

  return (
    <section className="panel">
      <h1>{doc.title || doc.external_ref}</h1>
      <dl className="meta-grid">
        <div>
          <dt>Regulator</dt>
          <dd>{doc.regulator_code}</dd>
        </div>
        <div>
          <dt>Source</dt>
          <dd>{doc.source_id}</dd>
        </div>
        <div>
          <dt>Status</dt>
          <dd>{doc.ingest_status}</dd>
        </div>
        <div>
          <dt>Language</dt>
          <dd>{doc.language}</dd>
        </div>
      </dl>
      <h2>Versions</h2>
      <div className="prop-list">
        {doc.versions.map((v) => (
          <div className="prop" key={v.id}>
            <div className="prop-type">
              v{v.version_number} · {v.sha256.slice(0, 12)}…
            </div>
            <p>
              <code>{v.storage_key}</code>
            </p>
          </div>
        ))}
      </div>
      <p>
        <Link href="/documents">Back</Link>
      </p>
    </section>
  );
}
