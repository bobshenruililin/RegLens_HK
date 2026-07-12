import Link from "next/link";
import { notFound } from "next/navigation";
import { ComparePanels } from "@/components/ComparePanels";
import { StatusNotice } from "@/components/StatusNotice";
import { StatuteText } from "@/components/RedlineView";
import {
  loadRootManifest,
  loadTransition,
  loadTransitionsIndex,
} from "@/lib/data";
import { relationshipLabel, snapshotPrimary } from "@/lib/format";
import { HKEL } from "@/lib/links";
import { countTokenDelta, type Op } from "@/lib/ops";

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

function navNeighbors(
  slug: string,
  from: string,
  to: string,
  sectionId: string,
) {
  const tid = `${from}__to__${to}`;
  const data = loadTransition(slug, tid) as {
    items: Array<{ section_id: string; relationship: string }>;
  };
  const changed = data.items.filter((i) => i.relationship !== "unchanged");
  const idx = changed.findIndex((i) => i.section_id === sectionId);
  const prev = idx > 0 ? changed[idx - 1] : null;
  const next = idx >= 0 && idx < changed.length - 1 ? changed[idx + 1] : null;
  return { prev, next, idx, total: changed.length };
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

  const rel = String(item.relationship);
  const isAdded = rel === "added";
  const isRemoved = rel === "removed";
  const delta = countTokenDelta(item.legal_text_ops as Op[] | undefined);
  const structDelta = countTokenDelta(item.structural_ops as Op[] | undefined);
  const metaDelta = countTokenDelta(item.metadata_ops as Op[] | undefined);
  const neighbors = navNeighbors(params.id, from, to, sectionId);

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

  const num = String(item.section_num_b || item.section_num_a || "—");

  return (
    <>
      <div className="sticky-bar">
        <div className="sticky-bar-inner">
          <div>
            <strong>{params.id.toUpperCase()}</strong> · § {num} ·{" "}
            <span className="pill">{relationshipLabel(rel)}</span>
          </div>
          <div className="meta">
            {snapshotPrimary(String(data.from_label), from)} →{" "}
            {snapshotPrimary(String(data.to_label), to)}
            {item.renderability_a
              ? ` · Renderability ${String(item.renderability_a)}→${String(item.renderability_b)}`
              : ""}
          </div>
        </div>
      </div>

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
        {neighbors.prev ? (
          <>
            {" · "}
            <Link
              href={`/instruments/${params.id}/sections/${encodeURIComponent(neighbors.prev.section_id)}/compare/${encodeURIComponent(from)}/${encodeURIComponent(to)}/`}
            >
              Previous changed
            </Link>
          </>
        ) : null}
        {neighbors.next ? (
          <>
            {" · "}
            <Link
              href={`/instruments/${params.id}/sections/${encodeURIComponent(neighbors.next.section_id)}/compare/${encodeURIComponent(from)}/${encodeURIComponent(to)}/`}
            >
              Next changed
            </Link>
          </>
        ) : null}
        {neighbors.idx >= 0 ? (
          <span className="meta">
            {" "}
            ({neighbors.idx + 1}/{neighbors.total})
          </span>
        ) : null}
      </p>

      <h1 className="page-title">Section comparator · § {num}</h1>
      <StatusNotice compact />

      <div className="summary-grid">
        <div>
          <strong>Tokens added</strong>
          <div>{delta.additions}</div>
        </div>
        <div>
          <strong>Tokens removed</strong>
          <div>{delta.deletions}</div>
        </div>
        <div>
          <strong>Text changed?</strong>
          <div>
            {rel.includes("text") || isAdded || isRemoved ? "Yes" : "No"}
          </div>
        </div>
        <div>
          <strong>Status changed?</strong>
          <div>
            {rel.includes("status") || metaDelta.additions + metaDelta.deletions > 0
              ? "Yes"
              : "No"}
          </div>
        </div>
        <div>
          <strong>Structure changed?</strong>
          <div>
            {structDelta.additions + structDelta.deletions > 0 ? "Yes" : "No"}
          </div>
        </div>
      </div>

      <p className="meta">
        A: {String(data.from_label)} (<code>{from}</code>)
        <br />
        B: {String(data.to_label)} (<code>{to}</code>)
        <br />
        Stable @id: <code>{sectionId}</code>
        <br />
        Reconstruction OK: {String(item.reconstruction_ok ?? true)}
        <br />
        Official portal:{" "}
        <a href={HKEL} rel="noreferrer">
          {HKEL}
        </a>
      </p>

      {isAdded ? (
        <>
          <h2 className="section-title">Added section</h2>
          <p>Classification: added.</p>
          <div className="side-by-side">
            <div>
              <h3>Snapshot A</h3>
              <p className="muted">Section not present in this snapshot.</p>
            </div>
            <div>
              <h3>Snapshot B</h3>
              <StatuteText text={String(item.plain_text_b || "")} />
            </div>
          </div>
        </>
      ) : null}

      {isRemoved ? (
        <>
          <h2 className="section-title">Removed section</h2>
          <p>Classification: removed.</p>
          <div className="side-by-side">
            <div>
              <h3>Snapshot A</h3>
              <StatuteText text={String(item.plain_text_a || "")} />
            </div>
            <div>
              <h3>Snapshot B</h3>
              <p className="muted">Section not present in this snapshot.</p>
            </div>
          </div>
        </>
      ) : null}

      {!isAdded && !isRemoved ? (
        <ComparePanels
          highlightLegalText={(item.highlight_legal_text as string[]) || []}
          plainTextA={String(item.plain_text_a || "")}
          plainTextB={String(item.plain_text_b || "")}
          metadataOps={item.metadata_ops}
          structuralOps={item.structural_ops}
          relationship={rel}
          numA={(item.section_num_a as string) || null}
          numB={(item.section_num_b as string) || null}
        />
      ) : (
        <details style={{ marginTop: "1rem" }}>
          <summary>Technical provenance</summary>
          <pre className="redline">
            {JSON.stringify(
              { provenance_a: item.provenance_a, provenance_b: item.provenance_b },
              null,
              2,
            )}
          </pre>
        </details>
      )}

      {!isAdded && !isRemoved ? (
        <>
          <h2 className="section-title">Provenance</h2>
          <div className="side-by-side">
            <pre className="redline">
              {JSON.stringify(item.provenance_a || {}, null, 2)}
            </pre>
            <pre className="redline">
              {JSON.stringify(item.provenance_b || {}, null, 2)}
            </pre>
          </div>
        </>
      ) : null}

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
      <p className="meta">
        Stable URL: this page path survives refresh. Copy from the browser
        address bar.
      </p>
    </>
  );
}
