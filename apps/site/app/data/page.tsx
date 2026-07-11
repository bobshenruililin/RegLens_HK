import { SyntheticBanner } from "@/components/SyntheticBanner";
import { loadChecksums, loadRelease, withBasePath } from "@/lib/release";

export const metadata = {
  title: "Data",
};

const DOWNLOADS = [
  { name: "release.json", label: "Release metadata" },
  { name: "catalog.json", label: "Decision catalog" },
  { name: "analytics.json", label: "Analytics aggregates" },
  { name: "decisions.csv", label: "Decisions CSV" },
  { name: "propositions.csv", label: "Propositions CSV" },
  { name: "checksums.sha256", label: "SHA-256 checksums" },
] as const;

export default function DataPage() {
  const release = loadRelease();
  const checksums = loadChecksums();
  const regulators = Array.isArray(release.regulators)
    ? release.regulators
    : Object.keys(release.regulators || {});

  return (
    <>
      <SyntheticBanner kind={release.kind} version={release.version} />

      <header className="page-hero">
        <h1>Release data</h1>
        <p className="lede">
          Download the versioned publication files that power this static site.
          Files live under <code>/data/release/</code>. Raw source documents are
          never included.
        </p>
      </header>

      <section className="section" aria-labelledby="meta-heading">
        <h2 id="meta-heading">Release metadata</h2>
        <dl className="detail-dl">
          <dt>Release ID</dt>
          <dd>
            <code>{release.release_id}</code>
          </dd>
          <dt>Mode</dt>
          <dd>
            <code>{release.release_mode}</code>
          </dd>
          <dt>Generated / released</dt>
          <dd>
            {release.generated_at}
            {release.released_at ? ` · ${release.released_at}` : ""}
          </dd>
          <dt>Decisions / propositions</dt>
          <dd>
            {release.decision_count} / {release.proposition_count}
          </dd>
          <dt>Regulators</dt>
          <dd>{regulators.join(", ") || "—"}</dd>
          <dt>Methodology / taxonomy</dt>
          <dd>
            {release.methodology_version || "—"} /{" "}
            {release.taxonomy_version || "—"}
          </dd>
          <dt>Source cutoff</dt>
          <dd>{release.source_cutoff_date || "—"}</dd>
        </dl>
        {release.description ? <p>{release.description}</p> : null}
        {(release.global_caveats || []).length > 0 ? (
          <ul>
            {release.global_caveats!.map((c) => (
              <li key={c}>{c}</li>
            ))}
          </ul>
        ) : null}
      </section>

      <section className="section" aria-labelledby="dl-heading">
        <h2 id="dl-heading">Downloads</h2>
        <ul className="decision-list">
          {DOWNLOADS.map((f) => (
            <li key={f.name} className="decision-card">
              <h3>
                <a href={withBasePath(`/data/release/${f.name}`)} download>
                  {f.label}
                </a>
              </h3>
              <p>
                <code>/data/release/{f.name}</code>
              </p>
            </li>
          ))}
        </ul>
      </section>

      <section className="section" aria-labelledby="sum-heading">
        <h2 id="sum-heading">Checksums</h2>
        <pre className="checksum-pre">{checksums.trim() || "(empty)"}</pre>
      </section>
    </>
  );
}
