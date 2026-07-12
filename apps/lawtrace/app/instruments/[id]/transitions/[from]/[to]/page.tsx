import Link from "next/link";
import { notFound } from "next/navigation";
import { StatusNotice } from "@/components/StatusNotice";
import {
  loadRootManifest,
  loadTransition,
  loadTransitionsIndex,
} from "@/lib/data";
import { relationshipLabel } from "@/lib/format";

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

  return (
    <>
      <p className="meta">
        <Link href={`/instruments/${params.id}/`}>← Instrument</Link>
      </p>
      <h1 className="page-title">Transition explorer</h1>
      <StatusNotice compact />
      <p>
        <strong>{String(data.from_label)}</strong>
        <br />→ <strong>{String(data.to_label)}</strong>
      </p>
      <p className="meta">
        Unchanged: {String(data.unchanged_count)} · Ambiguous (not accepted):{" "}
        {String(data.ambiguous_count)}
      </p>
      <p>
        {Object.entries(counts).map(([k, v]) => (
          <span key={k} className="pill" style={{ marginRight: "0.35rem" }}>
            {relationshipLabel(k)}: {v}
          </span>
        ))}
      </p>

      <h2 className="section-title">Changed / added / removed sections</h2>
      <div className="table-wrap" style={{ marginTop: "0.75rem" }}>
        <table className="data">
          <thead>
            <tr>
              <th>Section</th>
              <th>Class</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {changed.map((item) => {
              const sid = String(item.section_id);
              const rel = String(item.relationship);
              const num =
                (item.section_num_b as string) ||
                (item.section_num_a as string) ||
                "—";
              return (
                <tr key={`${sid}-${rel}`}>
                  <td>
                    § {num}
                    <div className="meta">
                      <code>{sid}</code>
                    </div>
                  </td>
                  <td>
                    <span
                      className={`pill ${
                        rel === "added"
                          ? "add"
                          : rel === "removed"
                            ? "del"
                            : rel.includes("status") && !rel.includes("text")
                              ? "status"
                              : ""
                      }`}
                    >
                      {relationshipLabel(rel)}
                    </span>
                  </td>
                  <td>
                    {rel === "added" || rel === "removed" ? (
                      <Link
                        href={`/instruments/${params.id}/sections/${encodeURIComponent(sid)}/`}
                      >
                        History
                      </Link>
                    ) : (
                      <Link
                        href={`/instruments/${params.id}/sections/${encodeURIComponent(sid)}/compare/${encodeURIComponent(from)}/${encodeURIComponent(to)}/`}
                      >
                        Compare
                      </Link>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </>
  );
}
