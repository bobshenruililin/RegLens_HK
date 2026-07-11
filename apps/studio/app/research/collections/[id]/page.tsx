import Link from "next/link";
import { notFound } from "next/navigation";
import { requireUser } from "../../../../lib/auth-server";
import {
  buildResearchCollectionExport,
  getResearchDecisionSummaries,
  getResearchCollection,
} from "../../../../lib/research-data";

export const dynamic = "force-dynamic";

export default async function ResearchCollectionDetailPage({
  params,
}: {
  params: { id: string };
}) {
  await requireUser();
  const collection = await getResearchCollection(params.id);
  if (!collection) notFound();
  const [decisions, exportBundle] = await Promise.all([
    getResearchDecisionSummaries(collection.decision_ids),
    buildResearchCollectionExport(collection.id),
  ]);

  return (
    <section className="panel">
      <p>
        <Link href="/research/collections">Research collections</Link>
      </p>
      <h1>{collection.title}</h1>
      <p>{collection.description}</p>
      <p className="warning">
        INTERNAL USE ONLY. Demo collection exports are synthetic examples and
        are not legal advice.
      </p>
      <dl className="meta-grid">
        <div>
          <dt>Collection id</dt>
          <dd>{collection.id}</dd>
        </div>
        <div>
          <dt>Decisions</dt>
          <dd>{collection.decision_ids.length}</dd>
        </div>
        <div>
          <dt>Updated</dt>
          <dd>{collection.updated_at}</dd>
        </div>
        <div>
          <dt>Store policy</dt>
          <dd>{collection.synthetic_only ? "synthetic only" : "internal"}</dd>
        </div>
      </dl>
      <p>
        <a href={`/api/research/collections/${collection.id}/export`}>
          Export Markdown+CSV JSON
        </a>
      </p>
      <h2>Decisions</h2>
      {decisions.length === 0 ? (
        <p>No reviewed decisions matched this collection.</p>
      ) : (
        <div className="prop-list">
          {decisions.map((decision) => (
            <div className="prop" key={decision.external_ref}>
              <div className="prop-type">
                {decision.regulator_code} · {decision.external_ref}
              </div>
              <p className="claim">{decision.title || decision.external_ref}</p>
              <p>{decision.takeaway}</p>
              {decision.id && (
                <Link href={`/research/compare?ids=${decision.id}`}>Compare</Link>
              )}
            </div>
          ))}
        </div>
      )}
      {exportBundle && (
        <details style={{ marginTop: "1rem" }}>
          <summary>Markdown preview</summary>
          <pre style={{ whiteSpace: "pre-wrap" }}>{exportBundle.markdown}</pre>
        </details>
      )}
    </section>
  );
}
