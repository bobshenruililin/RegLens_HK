import Link from "next/link";
import { listIssueIndex, loadTaxonomy } from "../../lib/research-data";

export const dynamic = "force-dynamic";

export default async function IssuesPage() {
  const taxonomy = loadTaxonomy();
  const issues = await listIssueIndex();

  return (
    <section className="panel">
      <h1>Issues</h1>
      <p>
        Taxonomy issue categories from{" "}
        <code>publications/taxonomy/taxonomy.v1.json</code> with reviewed
        decision counts from the active Studio data source.
      </p>
      <p className="prop-type">Taxonomy v{taxonomy.taxonomy_version}</p>
      <div className="prop-list">
        {issues.map((issue) => (
          <div className="prop" key={issue.code}>
            <div className="prop-type">
              {issue.code} · {issue.decision_count} decision
              {issue.decision_count === 1 ? "" : "s"}
            </div>
            <p className="claim">{issue.label}</p>
            <Link href={`/issues/${issue.code}`}>Open decisions</Link>
          </div>
        ))}
      </div>
    </section>
  );
}
