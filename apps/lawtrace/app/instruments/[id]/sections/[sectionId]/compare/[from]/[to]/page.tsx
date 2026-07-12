import Link from "next/link";
import { notFound } from "next/navigation";
import { RedlineView } from "@/components/RedlineView";
import { StatusNotice } from "@/components/StatusNotice";
import {
  loadRootManifest,
  loadTransition,
  loadTransitionsIndex,
} from "@/lib/data";
import { relationshipLabel } from "@/lib/format";
import { HKEL } from "@/lib/links";

export function generateStaticParams() {
  const params: Array<{ id: string; sectionId: string; from: string; to: string }> =
    [];
  for (const inst of loadRootManifest().instruments) {
    if (!inst.available) continue;
    const transitions = loadTransitionsIndex(inst.slug).transitions as Array<{
      transition_id: string;
      from_version: string;
      to_version: string;
    }>;
    for (const t of transitions) {
      const data = loadTransition(inst.slug, t.transition_id) as {
        items: Array<{ section_id: string; relationship: string }>;
      };
      for (const item of data.items) {
        if (item.relationship === "unchanged") continue;
        if (item.relationship === "added" || item.relationship === "removed") {
          continue;
        }
        params.push({
          id: inst.slug,
          sectionId: item.section_id,
          from: t.from_version,
          to: t.to_version,
        });
      }
    }
  }
  return params;
}

export default function ComparePage({
  params,
}: {
  params: { id: string; sectionId: string; from: string; to: string };
}) {
  const sectionId = decodeURIComponent(params.sectionId);
  const from = decodeURIComponent(params.from);
  const to = decodeURIComponent(params.to);
  const tid = `${from}__to__${to}`;
  let data: Record<string, unknown>;
  try {
    data = loadTransition(params.id, tid);
  } catch {
    notFound();
  }
  const item = (
    (data.items as Array<Record<string, unknown>>) || []
  ).find((i) => i.section_id === sectionId);
  if (!item) notFound();

  const downloadName = `${params.id}-${sectionId}-compare.json`;

  return (
    <>
      <p className="meta">
        <Link
          href={`/instruments/${params.id}/sections/${encodeURIComponent(sectionId)}/`}
        >
          ← Section history
        </Link>
        {" · "}
        <Link
          href={`/instruments/${params.id}/transitions/${encodeURIComponent(from)}/${encodeURIComponent(to)}/`}
        >
          Transition
        </Link>
      </p>
      <h1 className="page-title">
        Section comparator · §{" "}
        {String(item.section_num_b || item.section_num_a || "—")}
      </h1>
      <StatusNotice />
      <p>
        <span className="pill">{relationshipLabel(String(item.relationship))}</span>{" "}
        {item.ordinary_redline_supported ? null : (
          <span className="pill del">Ordinary redline limited</span>
        )}
      </p>
      <p className="meta">
        A: {String(data.from_label)} (<code>{from}</code>)
        <br />
        B: {String(data.to_label)} (<code>{to}</code>)
        <br />
        @id: <code>{sectionId}</code>
        <br />
        Renderability: {String(item.renderability_a)} → {String(item.renderability_b)}
        <br />
        Reconstruction OK: {String(item.reconstruction_ok)}
        <br />
        Official portal:{" "}
        <a href={HKEL} rel="noreferrer">
          {HKEL}
        </a>
      </p>

      <h2 className="section-title">Inline redline (legal-text channel)</h2>
      <RedlineView lines={(item.highlight_legal_text as string[]) || []} />

      <h2 className="section-title">Side-by-side canonical plain text</h2>
      <div className="side-by-side" style={{ marginTop: "0.75rem" }}>
        <div>
          <h3>Snapshot A</h3>
          <pre className="redline">{String(item.plain_text_a || "")}</pre>
        </div>
        <div>
          <h3>Snapshot B</h3>
          <pre className="redline">{String(item.plain_text_b || "")}</pre>
        </div>
      </div>

      <h2 className="section-title">Metadata / status channel</h2>
      <pre className="redline">
        {JSON.stringify(item.metadata_ops || [], null, 2)}
      </pre>
      <p className="meta">
        Status-only changes are listed here and are not presented as textual
        amendments.
      </p>

      <h2 className="section-title">Structural channel</h2>
      <pre className="redline">
        {JSON.stringify(item.structural_ops || [], null, 2)}
      </pre>

      <h2 className="section-title">Provenance</h2>
      <div className="side-by-side">
        <pre className="redline">{JSON.stringify(item.provenance_a || {}, null, 2)}</pre>
        <pre className="redline">{JSON.stringify(item.provenance_b || {}, null, 2)}</pre>
      </div>

      <p style={{ marginTop: "1rem" }}>
        <a
          className="btn secondary"
          href={`/data/instruments/${params.id}/transitions/${tid}.json`}
          download={downloadName}
        >
          Download transition JSON
        </a>
      </p>
    </>
  );
}
