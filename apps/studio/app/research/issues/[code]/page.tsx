import Link from "next/link";
import { requireUser } from "../../../../lib/auth-server";
import { getIssueDetail } from "../../../../lib/research-data";

export const dynamic = "force-dynamic";

export default async function ResearchIssueDetailPage({
  params,
}: {
  params: { code: string };
}) {
  await requireUser();
  const detail = await getIssueDetail(params.code);

  return (
    <section className="panel">
      <p>
        <Link href="/research/issues">Research issues</Link>
      </p>
      <h1>{detail.category?.label || params.code}</h1>
      <p className="prop-type">{params.code}</p>
      {detail.decisions.length === 0 && (
        <p>No reviewed synthetic/demo decisions currently share this issue.</p>
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
                <Link href={`/research/compare?ids=${decision.decision_id}`}>
                  Compare
                </Link>
                {" · "}
                <Link href={`/decisions/${decision.decision_id}`}>Open decision</Link>
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
