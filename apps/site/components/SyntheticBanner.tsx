type SyntheticBannerProps = {
  kind?: string;
  version?: string;
};

export function SyntheticBanner({ kind, version }: SyntheticBannerProps) {
  const synthetic =
    !kind || kind.toLowerCase().includes("synthetic") || kind === "synthetic_demo";

  if (!synthetic) return null;

  return (
    <aside className="banner" role="note" aria-label="Synthetic corpus notice">
      <strong>Synthetic demonstration corpus</strong>
      <p>
        This release{version ? ` (${version})` : ""} is marked{" "}
        <code>{kind || "synthetic_demo"}</code>. Counts, charts, and decision
        pages reflect demo fixtures only — not a complete or authoritative public
        archive of MCHK or DCHK decisions.
      </p>
    </aside>
  );
}
