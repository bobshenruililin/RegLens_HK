import { DISCLAIMER, DATE_NOTE } from "@/lib/disclaimer";

export function StatusNotice({ compact = false }: { compact?: boolean }) {
  return (
    <aside className="notice" role="note">
      <strong>Informational status</strong>
      <p style={{ margin: 0 }}>{DISCLAIMER}</p>
      {compact ? null : (
        <p className="muted" style={{ margin: "0.5rem 0 0" }}>
          {DATE_NOTE}
        </p>
      )}
    </aside>
  );
}
