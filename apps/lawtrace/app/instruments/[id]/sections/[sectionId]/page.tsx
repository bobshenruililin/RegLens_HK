import Link from "next/link";
import { notFound } from "next/navigation";
import { StatusNotice } from "@/components/StatusNotice";
import { loadRootManifest, loadSectionDetail, loadSections } from "@/lib/data";
import { FREQUENCY_NOTE } from "@/lib/disclaimer";
import { relationshipLabel } from "@/lib/format";

export function generateStaticParams() {
  const params: Array<{ id: string; sectionId: string }> = [];
  for (const inst of loadRootManifest().instruments) {
    if (!inst.available) continue;
    const sections = loadSections(inst.slug).sections as Array<{ section_id: string }>;
    for (const s of sections) {
      params.push({ id: inst.slug, sectionId: s.section_id });
    }
  }
  return params;
}

export default function SectionHistoryPage({
  params,
}: {
  params: { id: string; sectionId: string };
}) {
  const sectionId = decodeURIComponent(params.sectionId);
  let detail: Record<string, unknown>;
  try {
    detail = loadSectionDetail(params.id, sectionId);
  } catch {
    notFound();
  }
  const snapshots = detail.snapshots as Record<
    string,
    { num?: string; heading?: string; status?: string; renderability?: string }
  >;
  const historyRows = (
    (detail.change_events as Array<{
      from_version: string;
      to_version: string;
      from_label: string;
      to_label: string;
      relationship: string;
    }>) || []
  ).filter((r) => r.relationship !== "unchanged");

  const latest = Object.values(snapshots).at(-1);

  return (
    <>
      <p className="meta">
        <Link href={`/instruments/${params.id}/`}>← Instrument</Link>
      </p>
      <h1 className="page-title">
        Section history · § {latest?.num || "—"}
      </h1>
      <p className="lede">{latest?.heading}</p>
      <StatusNotice variant="inline" />
      <p className="meta">
        Stable @id: <code>{sectionId}</code>
        <br />
        Descriptive change count:{" "}
        <strong>{String(detail.descriptive_change_count)}</strong>
      </p>
      <p className="meta">{FREQUENCY_NOTE}</p>

      <h2 className="section-title">Appearances by snapshot</h2>
      <div className="table-wrap" style={{ marginTop: "0.75rem" }}>
        <table className="data">
          <thead>
            <tr>
              <th>Snapshot</th>
              <th>Number</th>
              <th>Status</th>
              <th>Renderability</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(snapshots).map(([vid, snap]) => (
              <tr key={vid}>
                <td>
                  <code>{vid}</code>
                </td>
                <td>{snap.num}</td>
                <td>{snap.status || "—"}</td>
                <td>{snap.renderability}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <h2 className="section-title">Transitions where this section changed</h2>
      <div className="table-wrap" style={{ marginTop: "0.75rem" }}>
        <table className="data">
          <thead>
            <tr>
              <th>Transition</th>
              <th>Class</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {historyRows.map((r) => (
              <tr key={`${r.from_version}-${r.to_version}-${r.relationship}`}>
                <td>
                  <div>{r.from_label}</div>
                  <div className="meta">→ {r.to_label}</div>
                </td>
                <td>{relationshipLabel(r.relationship)}</td>
                <td>
                  <Link
                    href={`/instruments/${params.id}/sections/${encodeURIComponent(sectionId)}/compare/${encodeURIComponent(r.from_version)}/${encodeURIComponent(r.to_version)}/`}
                  >
                    Compare
                  </Link>
                </td>
              </tr>
            ))}
            {!historyRows.length ? (
              <tr>
                <td colSpan={3} className="muted">
                  No textual/status changes across included consecutive transitions.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </>
  );
}
