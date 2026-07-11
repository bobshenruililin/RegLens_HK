import Link from "next/link";
import { getMode, isDemoMode, isPostgresMode } from "../../lib/mode";
import { demoDashboardCounts } from "../../lib/policies";
import { getDashboardCounts } from "../../lib/pg-data";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  const mode = getMode();
  let counts;
  if (isPostgresMode()) {
    try {
      counts = await getDashboardCounts();
    } catch (err) {
      const message = err instanceof Error ? err.message : "DB error";
      return (
        <section className="panel">
          <p className="warning">
            Internal Studio — postgres mode failed: {message}
          </p>
          <h1>Dashboard</h1>
          <p>
            Mode: <code>{mode}</code>. Check <code>DATABASE_URL</code>.
          </p>
        </section>
      );
    }
  } else {
    counts = demoDashboardCounts();
  }

  return (
    <section className="panel">
      <p className="warning">
        RegLens Studio — internal operator tool. Not deployed to GitHub Pages.
        Mode: <code>{mode}</code>
        {isDemoMode() ? (
          <>
            {" "}
            · reads/writes <code>data/seed</code> only.
          </>
        ) : (
          <> · operational source of truth is PostgreSQL.</>
        )}
      </p>
      <h1>Dashboard</h1>
      <p>
        Counts for the active Studio data plane. Public Observatory never reads
        this surface.
      </p>
      <dl className="meta-grid">
        <div>
          <dt>Decisions</dt>
          <dd>{counts.decisions}</dd>
        </div>
        <div>
          <dt>Documents</dt>
          <dd>{counts.documents}</dd>
        </div>
        <div>
          <dt>Review queue</dt>
          <dd>{counts.reviewsPending}</dd>
        </div>
        <div>
          <dt>Jobs pending</dt>
          <dd>{counts.jobsPending}</dd>
        </div>
        <div>
          <dt>Jobs running</dt>
          <dd>{counts.jobsRunning}</dd>
        </div>
        <div>
          <dt>Releases</dt>
          <dd>{counts.releases}</dd>
        </div>
        <div>
          <dt>Audit events</dt>
          <dd>{counts.auditEvents}</dd>
        </div>
        {"publishedPropositions" in counts && (
          <div>
            <dt>Published propositions (demo)</dt>
            <dd>{(counts as { publishedPropositions: number }).publishedPropositions}</dd>
          </div>
        )}
      </dl>
      <p>
        <Link href="/review">Review</Link>
        {" · "}
        <Link href="/jobs">Jobs</Link>
        {" · "}
        <Link href="/releases">Releases</Link>
        {" · "}
        <Link href="/search">Search</Link>
      </p>
    </section>
  );
}
