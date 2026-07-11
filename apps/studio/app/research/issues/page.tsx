import Link from "next/link";
import { requireUser } from "../../../lib/auth-server";
import { listIssueIndex, loadTaxonomy } from "../../../lib/research-data";

export const dynamic = "force-dynamic";

export default async function ResearchIssuesPage() {
  await requireUser();
  const taxonomy = loadTaxonomy();
  const issues = await listIssueIndex();

  return (
    <section className="panel">
      <h1>Research issues</h1>
      <p>
        Issue taxonomy for the internal research surface, counted from reviewed
        synthetic/demo annotations.
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
            <Link href={`/research/issues/${issue.code}`}>Open issue detail</Link>
          </div>
        ))}
      </div>
    </section>
  );
}
