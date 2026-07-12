import { DISCLAIMER, DATE_NOTE } from "@/lib/disclaimer";

export function StatusNotice({ compact = false }: { compact?: boolean }) {
  return (
    <aside className="notice" role="note">
      <strong>Informational status</strong>
      <p style={{ margin: 0 }}>{DISCLAIMER}</p>
      <p className="muted" style={{ margin: "0.5rem 0 0" }}>
        {compact
          ? "Snapshot dates identify official open-data XML versions, not commencement or effective dates."
          : DATE_NOTE}
      </p>
    </aside>
  );
}
