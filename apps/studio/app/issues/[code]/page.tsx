import Link from "next/link";
import { getIssueDetail } from "../../../lib/research-data";

export const dynamic = "force-dynamic";

export default async function IssueDetailPage({
  params,
}: {
  params: { code: string };
}) {
  const detail = await getIssueDetail(params.code);

  return (
    <section className="panel">
      <p>
        <Link href="/issues">Issues</Link>
      </p>
      <h1>{detail.category?.label || params.code}</h1>
      <p className="prop-type">{params.code}</p>
      {detail.decisions.length === 0 && (
        <p>No reviewed decisions currently share this issue.</p>
      )}
      <div className="prop-list">
        {detail.decisions.map((decision) => (
          <div className="prop" key={decision.external_ref}>
            <div className="prop-type">
              {decision.regulator_code} · {decision.profession || "unknown"} ·{" "}
              {decision.reviewer_status}
            </div>
            <p className="claim">{decision.title || decision.external_ref}</p>
            <p>{decision.summary}</p>
            <p style={{ color: "var(--muted)" }}>{decision.takeaway}</p>
            {decision.decision_id ? (
              <>
                <Link href={`/decisions/${decision.decision_id}`}>Open decision</Link>
                {" · "}
                <Link href={`/review/${decision.decision_id}`}>Review</Link>
              </>
            ) : (
              <span className="badge">Annotation only</span>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}
