import Link from "next/link";
import { notFound } from "next/navigation";
import { StatusNotice } from "@/components/StatusNotice";
import { SearchList } from "@/components/SearchList";
import {
  loadInstrumentManifest,
  loadRootManifest,
  loadSections,
  loadTransitionsIndex,
  loadVersions,
} from "@/lib/data";
import { relationshipLabel } from "@/lib/format";

export function generateStaticParams() {
  return loadRootManifest().instruments.map((i) => ({ id: i.slug }));
}

export default function InstrumentPage({ params }: { params: { id: string } }) {
  const root = loadRootManifest();
  const card = root.instruments.find((i) => i.slug === params.id);
  if (!card) notFound();

  if (!card.available) {
    return (
      <>
        <h1 className="page-title">{card.title}</h1>
        <StatusNotice />
        <div className="card" style={{ marginTop: "1rem" }}>
          <p>{card.missing_reason}</p>
          <p className="meta">
            After official Cap. 599G extracts are available locally, run{" "}
            <code>make lawtrace-web-data-local</code>.
          </p>
        </div>
      </>
    );
  }

  const manifest = loadInstrumentManifest(params.id) as {
    title: string;
    version_count: number;
    section_count: number;
    relationship_totals: Record<string, number>;
    sampling: { complete: boolean; total_available_versions: number; versions_included: number };
    reconstruction: { ok: number; total: number; rate: number };
  };
  const versions = loadVersions(params.id).versions as Array<{
    version_id: string;
    snapshot_label: string;
    top_level_section_count: number;
  }>;
  const transitions = loadTransitionsIndex(params.id).transitions as Array<{
    transition_id: string;
    from_version: string;
    to_version: string;
    from_label: string;
    to_label: string;
    changed_count: number;
    counts: Record<string, number>;
  }>;
  const sections = loadSections(params.id).sections as Array<{
    section_id: string;
    latest_num?: string;
    latest_heading?: string;
    descriptive_change_count: number;
    nums_seen: string[];
    headings_seen: string[];
  }>;

  const searchItems = sections.map((s) => ({
    href: `/instruments/${params.id}/sections/${encodeURIComponent(s.section_id)}/`,
    title: `§ ${s.latest_num || s.nums_seen[0] || "—"}`,
    subtitle: `${s.latest_heading || ""} · descriptive changes: ${s.descriptive_change_count}`,
    haystack: [s.section_id, ...(s.nums_seen || []), ...(s.headings_seen || [])].join(" "),
  }));

  return (
    <>
      <h1 className="page-title">{manifest.title || card.title}</h1>
      <StatusNotice compact />
      <p className="meta" style={{ marginTop: "1rem" }}>
        {manifest.version_count} snapshots
        {!manifest.sampling?.complete
          ? ` (sampled ${manifest.sampling.versions_included} of ${manifest.sampling.total_available_versions} available — not a complete corpus)`
          : " (complete for this export)"}{" "}
        · {manifest.section_count} top-level sections · reconstruction{" "}
        {manifest.reconstruction.ok}/{manifest.reconstruction.total}
      </p>

      <h2 className="section-title">Snapshot timeline</h2>
      <div className="table-wrap" style={{ margin: "0.75rem 0 1.5rem" }}>
        <table className="data">
          <thead>
            <tr>
              <th>Snapshot</th>
              <th>Sections</th>
            </tr>
          </thead>
          <tbody>
            {versions.map((v) => (
              <tr key={v.version_id}>
                <td>
                  {v.snapshot_label}
                  <div className="meta">
                    <code>{v.version_id}</code>
                  </div>
                </td>
                <td>{v.top_level_section_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <h2 className="section-title">Transitions (consecutive only)</h2>
      <div className="table-wrap" style={{ margin: "0.75rem 0 1.5rem" }}>
        <table className="data">
          <thead>
            <tr>
              <th>From → To</th>
              <th>Changed</th>
              <th>Classes</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {transitions.map((t) => (
              <tr key={t.transition_id}>
                <td>
                  <div>{t.from_label}</div>
                  <div className="meta">→ {t.to_label}</div>
                </td>
                <td>{t.changed_count}</td>
                <td className="meta">
                  {Object.entries(t.counts)
                    .filter(([k]) => k !== "unchanged")
                    .map(([k, v]) => `${relationshipLabel(k)}: ${v}`)
                    .join(" · ") || "—"}
                </td>
                <td>
                  <Link
                    href={`/instruments/${params.id}/transitions/${encodeURIComponent(t.from_version)}/${encodeURIComponent(t.to_version)}/`}
                  >
                    Open
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <h2 className="section-title">Sections</h2>
      <SearchList items={searchItems} placeholder="Filter sections by number, heading, or @id" />
    </>
  );
}
