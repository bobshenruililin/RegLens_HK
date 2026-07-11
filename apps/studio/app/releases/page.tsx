import Link from "next/link";
import { isDemoMode, isPostgresMode } from "../../lib/mode";
import { listReleases } from "../../lib/pg-data";

export const dynamic = "force-dynamic";

export default async function ReleasesPage() {
  if (isDemoMode()) {
    return (
      <section className="panel">
        <h1>Releases</h1>
        <p className="warning">
          Publication releases require <code>REGLENS_MODE=postgres</code>. Demo
          mode builds Observatory bundles via <code>make demo-release</code> /
          worker CLI, not this UI.
        </p>
      </section>
    );
  }

  if (!isPostgresMode()) {
    return (
      <section className="panel">
        <h1>Releases</h1>
        <p className="warning">Unsupported mode.</p>
      </section>
    );
  }

  const releases = await listReleases();
  return (
    <section className="panel">
      <h1>Releases</h1>
      <p>Trusted publication transactions (PostgreSQL).</p>
      {releases.length === 0 && <p>No releases.</p>}
      <div className="prop-list">
        {releases.map((r) => (
          <div className="prop" key={r.id}>
            <div className="prop-type">
              {r.release_mode} · {r.status} · v{r.version}
            </div>
            <p className="claim">{r.title}</p>
            <p>
              <Link href={`/releases/${r.release_id}`}>{r.release_id}</Link>
              {" · "}
              {r.decision_count} decisions
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}
