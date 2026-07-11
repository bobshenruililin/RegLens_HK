import Link from "next/link";
import { requireUser } from "../../../lib/auth-server";
import {
  listResearchCollections,
  listResearchDecisionOptions,
} from "../../../lib/research-data";

export const dynamic = "force-dynamic";

export default async function ResearchCollectionsPage() {
  await requireUser();
  const [collections, decisions] = await Promise.all([
    listResearchCollections(),
    listResearchDecisionOptions(),
  ]);

  return (
    <section className="panel">
      <h1>Research collections</h1>
      <p>
        Demo collections are file-backed JSON under{" "}
        <code>data/research-collections/</code> and must contain synthetic
        examples only. Use the API to create additional demo collections.
      </p>
      <details className="checklist">
        <summary>Create via API</summary>
        <pre>{`POST /api/research/collections
{
  "title": "Synthetic collection",
  "description": "Internal demo collection",
  "decision_ids": ["${decisions[0]?.id || "decision-id"}"]
}`}</pre>
      </details>
      {collections.length === 0 ? (
        <p className="warning">No demo collections found.</p>
      ) : (
        <div className="prop-list">
          {collections.map((collection) => (
            <div className="prop" key={collection.id}>
              <div className="prop-type">
                {collection.id} · {collection.decision_ids.length} decision
                {collection.decision_ids.length === 1 ? "" : "s"}
              </div>
              <p className="claim">{collection.title}</p>
              <p>{collection.description}</p>
              {collection.synthetic_only && <span className="badge">synthetic only</span>}
              <Link href={`/research/collections/${collection.id}`}>Open collection</Link>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
