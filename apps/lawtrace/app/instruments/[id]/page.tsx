import Link from "next/link";
import { notFound } from "next/navigation";
import { StatusNotice } from "@/components/StatusNotice";
import { SectionTable } from "@/components/SectionTable";
import {
  loadInstrumentManifest,
  loadRootManifest,
  loadSections,
  loadTransitionsIndex,
  loadVersions,
} from "@/lib/data";
import { FREQUENCY_NOTE } from "@/lib/disclaimer";
import { instrumentCompletenessBadge } from "@/lib/mode";

export function generateStaticParams() {
  return loadRootManifest().instruments.map((i) => ({ id: i.slug }));
}

export default function InstrumentPage({ params }: { params: { id: string } }) {
  const root = loadRootManifest();
  const card = root.instruments.find((i) => i.slug === params.id);
  if (!card) notFound();
  const badge = instrumentCompletenessBadge(card);

  if (!card.available) {
    return (
      <>
        <h1 className="page-title">{card.title}</h1>
        {badge ? (
          <span className={`mode-badge tone-${badge.tone}`}>{badge.label}</span>
        ) : null}
        <StatusNotice />
        <div className="card" style={{ marginTop: "1rem" }}>
          <p>{card.missing_reason}</p>
          <p className="meta">
            After official Cap. 599G extracts are available locally, run{" "}
            <code>make lawtrace-web-data-local</code> then{" "}
            <code>make lawtrace-preview-local</code>.
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
    sampling: {
      complete: boolean;
      total_available_versions: number;
      versions_included: number;
    };
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

  const maxChanged = Math.max(1, ...transitions.map((t) => t.changed_count));
  const mostActive = [...sections]
    .sort((a, b) => b.descriptive_change_count - a.descriptive_change_count)
    .slice(0, 8);

  return (
    <>
      <div className="card-head">
        <h1 className="page-title">{manifest.title || card.title}</h1>
        {badge ? (
          <span className={`mode-badge tone-${badge.tone}`}>{badge.label}</span>
        ) : null}
      </div>
      <StatusNotice variant="inline" />
      <p className="meta">
        {manifest.version_count} snapshots · {manifest.section_count} tracked
        top-level sections · Reconstruction {manifest.reconstruction.ok}/
        {manifest.reconstruction.total}
        {!manifest.sampling.complete
          ? ` · Sampled ${manifest.sampling.versions_included}/${manifest.sampling.total_available_versions} (not complete)`
          : " · Complete for available snapshots"}
      </p>

      <h2 className="section-title">Snapshot timeline</h2>
      <ol className="timeline">
        {versions.map((v) => (
          <li key={v.version_id}>
            <strong>{v.snapshot_label}</strong>
            <div className="meta">
              {v.top_level_section_count} top-level sections ·{" "}
              <code>{v.version_id}</code>
            </div>
          </li>
        ))}
      </ol>

      <h2 className="section-title">Change activity by transition</h2>
      {transitions.map((t) => (
        <div className="bar-row" key={t.transition_id}>
          <div className="meta">
            <Link
              href={`/instruments/${params.id}/transitions/${encodeURIComponent(t.from_version)}/${encodeURIComponent(t.to_version)}/`}
            >
              {t.to_label.replace("Official open-data snapshot dated ", "→ ")}
            </Link>
          </div>
          <div className="bar" aria-hidden="true">
            <span style={{ width: `${(100 * t.changed_count) / maxChanged}%` }} />
          </div>
          <div>{t.changed_count}</div>
        </div>
      ))}

      <h2 className="section-title">Most active sections</h2>
      <p className="meta">{FREQUENCY_NOTE}</p>
      <ul className="plain-list">
        {mostActive.map((s) => (
          <li key={s.section_id}>
            <Link
              href={`/instruments/${params.id}/sections/${encodeURIComponent(s.section_id)}/`}
            >
              § {s.latest_num || "—"} {s.latest_heading}
            </Link>{" "}
            <span className="meta">({s.descriptive_change_count})</span>
          </li>
        ))}
      </ul>

      <h2 className="section-title">Sections</h2>
      <SectionTable instrumentId={params.id} sections={sections} />
    </>
  );
}
