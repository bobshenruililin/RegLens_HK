import Link from "next/link";
import { notFound } from "next/navigation";
import { StatusNotice } from "@/components/StatusNotice";
import { TransitionFilter } from "@/components/TransitionFilter";
import {
  loadRootManifest,
  loadTransition,
  loadTransitionsIndex,
} from "@/lib/data";
import { countTokenDelta, type Op } from "@/lib/ops";

export function generateStaticParams() {
  const params: Array<{ id: string; from: string; to: string }> = [];
  for (const inst of loadRootManifest().instruments) {
    if (!inst.available) continue;
    const transitions = loadTransitionsIndex(inst.slug).transitions as Array<{
      from_version: string;
      to_version: string;
    }>;
    for (const t of transitions) {
      params.push({ id: inst.slug, from: t.from_version, to: t.to_version });
    }
  }
  return params;
}

export default function TransitionPage({
  params,
}: {
  params: { id: string; from: string; to: string };
}) {
  const from = decodeURIComponent(params.from);
  const to = decodeURIComponent(params.to);
  const tid = `${from}__to__${to}`;
  let data: Record<string, unknown>;
  try {
    data = loadTransition(params.id, tid);
  } catch {
    notFound();
  }

  const items = (data.items as Array<Record<string, unknown>>) || [];
  const counts = (data.counts as Record<string, number>) || {};
  const changed = items.filter((i) => i.relationship !== "unchanged");

  let tokenAdd = 0;
  let tokenDel = 0;
  for (const item of changed) {
    const d = countTokenDelta(item.legal_text_ops as Op[] | undefined);
    tokenAdd += d.additions;
    tokenDel += d.deletions;
  }

  const rows = changed.map((item) => {
    const sid = String(item.section_id);
    const rel = String(item.relationship);
    const href = `/instruments/${params.id}/sections/${encodeURIComponent(sid)}/compare/${encodeURIComponent(from)}/${encodeURIComponent(to)}/`;
    return {
      section_id: sid,
      relationship: rel,
      section_num_a: (item.section_num_a as string) || null,
      section_num_b: (item.section_num_b as string) || null,
      heading: (item.heading as string) || null,
      legal_text_ops: (item.legal_text_ops as Op[]) || [],
      href,
    };
  });

  return (
    <>
      <p className="meta">
        <Link href={`/instruments/${params.id}/`}>← Instrument</Link>
      </p>
      <h1 className="page-title">Transition explorer</h1>
      <StatusNotice variant="inline" />
      <p>
        <strong>{String(data.from_label)}</strong>
        <br />→ <strong>{String(data.to_label)}</strong>
      </p>
      <p className="meta">
        Unchanged: {String(data.unchanged_count)} · Ambiguous (not accepted):{" "}
        {String(data.ambiguous_count)} · Legal-text token flow: +{tokenAdd} / −
        {tokenDel}
      </p>
      <p>
        {Object.entries(counts).map(([k, v]) => (
          <span key={k} className="pill" style={{ marginRight: "0.35rem" }}>
            {k}: {v}
          </span>
        ))}
      </p>

      <h2 className="section-title">Changed / added / removed sections</h2>
      <TransitionFilter
        rows={rows}
        unchangedCount={Number(data.unchanged_count || 0)}
      />
    </>
  );
}
