import Link from "next/link";
import { notFound } from "next/navigation";
import { ComparePanels } from "@/components/ComparePanels";
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

  const comparisonPayload = {
    instrument_id: data.instrument_id,
    transition_id: tid,
    from_version: from,
    to_version: to,
    from_label: data.from_label,
    to_label: data.to_label,
    section: item,
    disclaimer:
      "Informational comparison of official open-data snapshots only. Not a verified copy.",
  };
  const downloadHref = `data:application/json;charset=utf-8,${encodeURIComponent(
    JSON.stringify(comparisonPayload, null, 2),
  )}`;
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
        Deep link: this page URL (survives refresh)
        <br />
        Official portal:{" "}
        <a href={HKEL} rel="noreferrer">
          {HKEL}
        </a>
      </p>

      <ComparePanels
        highlightLegalText={(item.highlight_legal_text as string[]) || []}
        plainTextA={String(item.plain_text_a || "")}
        plainTextB={String(item.plain_text_b || "")}
        metadataOps={item.metadata_ops}
        structuralOps={item.structural_ops}
        relationship={String(item.relationship)}
      />

      <h2 className="section-title">Provenance</h2>
      <div className="side-by-side">
        <pre className="redline">{JSON.stringify(item.provenance_a || {}, null, 2)}</pre>
        <pre className="redline">{JSON.stringify(item.provenance_b || {}, null, 2)}</pre>
      </div>

      <p style={{ marginTop: "1rem" }}>
        <a className="btn secondary" href={downloadHref} download={downloadName}>
          Download comparison JSON
        </a>{" "}
        <a
          className="btn secondary"
          href={`/data/instruments/${params.id}/transitions/${tid}.json`}
          download={`${params.id}-transition.json`}
        >
          Download full transition JSON
        </a>
      </p>
    </>
  );
}
