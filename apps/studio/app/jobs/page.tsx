import Link from "next/link";
import { isPostgresMode } from "../../lib/mode";
import { listJobs } from "../../lib/pg-data";

export const dynamic = "force-dynamic";

export default async function JobsPage() {
  if (!isPostgresMode()) {
    return (
      <section className="panel">
        <h1>Jobs</h1>
        <p className="warning">
          Job queue listing requires <code>REGLENS_MODE=postgres</code> and{" "}
          <code>DATABASE_URL</code>. Demo mode uses the file/demo worker path
          outside this UI.
        </p>
      </section>
    );
  }

  let jobs;
  try {
    jobs = await listJobs();
  } catch (err) {
    const message = err instanceof Error ? err.message : "DB error";
    return (
      <section className="panel">
        <h1>Jobs</h1>
        <p className="warning">{message}</p>
      </section>
    );
  }

  return (
    <section className="panel">
      <h1>Jobs</h1>
      <p>Lease/retry worker queue (PostgreSQL).</p>
      {jobs.length === 0 && <p>No jobs.</p>}
      <div className="prop-list">
        {jobs.map((job) => (
          <div className="prop" key={job.id}>
            <div className="prop-type">
              {job.job_type} · {job.status} · attempts {job.attempts}/
              {job.max_attempts}
            </div>
            <p className="claim">
              <code>{job.dedupe_key}</code>
            </p>
            {job.last_error && (
              <p className="warning" style={{ marginTop: "0.5rem" }}>
                {job.last_error}
              </p>
            )}
            <p style={{ color: "var(--muted)", fontSize: "0.85rem" }}>
              created {String(job.created_at)} · id{" "}
              <Link href={`/jobs#${job.id}`}>{job.id.slice(0, 8)}</Link>
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}
