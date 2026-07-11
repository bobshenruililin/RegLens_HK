import Link from "next/link";
import { ReleaseApproveButton } from "../../../components/ReleaseApproveButton";
import { isDemoMode, isPostgresMode } from "../../../lib/mode";
import { getRelease } from "../../../lib/pg-data";

export const dynamic = "force-dynamic";

export default async function ReleaseDetailPage({
  params,
}: {
  params: { "release-id": string };
}) {
  if (isDemoMode()) {
    return (
      <section className="panel">
        <h1>Release</h1>
        <p className="warning">Postgres mode required.</p>
      </section>
    );
  }
  if (!isPostgresMode()) {
    return (
      <section className="panel">
        <h1>Release</h1>
        <p className="warning">Unsupported mode.</p>
      </section>
    );
  }

  const release = await getRelease(params["release-id"]);
  if (!release) {
    return (
      <section className="panel">
        <h1>Release not found</h1>
      </section>
    );
  }

  return (
    <section className="panel">
      <h1>{release.title}</h1>
      <dl className="meta-grid">
        <div>
          <dt>Release id</dt>
          <dd>{release.release_id}</dd>
        </div>
        <div>
          <dt>Mode</dt>
          <dd>{release.release_mode}</dd>
        </div>
        <div>
          <dt>Status</dt>
          <dd>{release.status}</dd>
        </div>
        <div>
          <dt>Version</dt>
          <dd>{release.version}</dd>
        </div>
      </dl>
      <p>{release.description}</p>
      <p style={{ color: "var(--muted)" }}>
        Approve runs fail-closed SQL checks (accepted/edited revisions +
        evidence + editorial annotations), then sets status to{" "}
        <code>ready</code>. Artifact build remains a separate worker step.
      </p>
      <ReleaseApproveButton
        publicationReleaseId={release.id}
        expectedVersion={release.version}
        disabled={!["draft", "ready", "failed"].includes(release.status)}
      />
      <h2 style={{ marginTop: "1.5rem" }}>Items</h2>
      <div className="prop-list">
        {release.items.map((item) => (
          <div className="prop" key={item.id}>
            <div className="prop-type">
              {item.included ? "included" : "excluded"} · {item.public_slug}
            </div>
            <p className="claim">{item.decision_title || item.external_ref}</p>
            <Link href={`/decisions/${item.decision_id}`}>Decision</Link>
          </div>
        ))}
      </div>
      <p>
        <Link href="/releases">Back</Link>
      </p>
    </section>
  );
}
