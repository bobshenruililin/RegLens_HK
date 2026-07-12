import { DISCLAIMER, DATE_NOTE } from "@/lib/disclaimer";

/** Compact limitation callout — product first, then trust context. */
export function StatusNotice({
  compact = false,
  variant = "default",
}: {
  compact?: boolean;
  variant?: "default" | "inline";
}) {
  if (variant === "inline") {
    return (
      <p className="trust-inline" role="note">
        {DATE_NOTE}
      </p>
    );
  }
  return (
    <aside className={`notice ${compact ? "notice-compact" : ""}`} role="note">
      <strong>Open-data snapshot limitation</strong>
      <p style={{ margin: "0.35rem 0 0" }}>
        {compact
          ? "Snapshot dates identify official open-data XML versions, not commencement or effective dates."
          : DATE_NOTE}
      </p>
      {compact ? null : (
        <p className="muted" style={{ margin: "0.5rem 0 0" }}>
          {DISCLAIMER}
        </p>
      )}
    </aside>
  );
}
