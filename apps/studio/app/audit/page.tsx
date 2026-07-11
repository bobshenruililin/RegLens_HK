import { isDemoMode, isPostgresMode } from "../../lib/mode";
import { listAuditEvents } from "../../lib/pg-data";

export const dynamic = "force-dynamic";

export default async function AuditPage() {
  if (isDemoMode()) {
    return (
      <section className="panel">
        <h1>Audit</h1>
        <p className="warning">
          No audit_events in demo mode. Switch to{" "}
          <code>REGLENS_MODE=postgres</code> to list recent events.
        </p>
      </section>
    );
  }

  if (!isPostgresMode()) {
    return (
      <section className="panel">
        <h1>Audit</h1>
        <p className="warning">Unsupported mode.</p>
      </section>
    );
  }

  const events = await listAuditEvents();
  return (
    <section className="panel">
      <h1>Audit</h1>
      <p>Recent append-only operational events.</p>
      {events.length === 0 && <p>No events yet.</p>}
      <div className="prop-list">
        {events.map((e) => (
          <div className="prop" key={e.id}>
            <div className="prop-type">
              {e.action} · {e.entity_type}
            </div>
            <p className="claim">
              {e.actor} → <code>{e.entity_id}</code>
            </p>
            <p style={{ color: "var(--muted)", fontSize: "0.85rem" }}>
              {String(e.at)}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}
