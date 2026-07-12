"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { relationshipLabel, sectionSortKey } from "@/lib/format";
import { countTokenDelta, type Op } from "@/lib/ops";

export type TransitionRow = {
  section_id: string;
  relationship: string;
  section_num_a?: string | null;
  section_num_b?: string | null;
  heading?: string | null;
  legal_text_ops?: Op[];
  href: string;
};

export function TransitionFilter({
  rows,
  unchangedCount,
}: {
  rows: TransitionRow[];
  unchangedCount: number;
}) {
  const [q, setQ] = useState("");
  const [cls, setCls] = useState("all");
  const [sort, setSort] = useState<"num" | "type" | "tokens">("num");

  const filtered = useMemo(() => {
    let list = rows.filter((r) => {
      if (cls !== "all" && r.relationship !== cls) return false;
      const hay = [
        r.section_id,
        r.section_num_a,
        r.section_num_b,
        r.heading,
        r.relationship,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
      return !q || hay.includes(q.toLowerCase());
    });
    list = [...list].sort((a, b) => {
      if (sort === "type") return a.relationship.localeCompare(b.relationship);
      if (sort === "tokens") {
        const ta = countTokenDelta(a.legal_text_ops);
        const tb = countTokenDelta(b.legal_text_ops);
        return tb.additions + tb.deletions - (ta.additions + ta.deletions);
      }
      return sectionSortKey(a.section_num_b || a.section_num_a).localeCompare(
        sectionSortKey(b.section_num_b || b.section_num_a),
      );
    });
    return list;
  }, [rows, q, cls, sort]);

  return (
    <div>
      <div className="toolbar">
        <label className="visually-hidden" htmlFor="tr-q">
          Filter sections
        </label>
        <input
          id="tr-q"
          type="search"
          placeholder="Filter by section number, heading, or @id"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <label>
          Class{" "}
          <select value={cls} onChange={(e) => setCls(e.target.value)}>
            <option value="all">All changed</option>
            <option value="text_changed">Text changed</option>
            <option value="status_changed">Status only</option>
            <option value="text_and_status_changed">Text and status</option>
            <option value="added">Added</option>
            <option value="removed">Removed</option>
          </select>
        </label>
        <label>
          Sort{" "}
          <select
            value={sort}
            onChange={(e) => setSort(e.target.value as typeof sort)}
          >
            <option value="num">Section number</option>
            <option value="type">Change type</option>
            <option value="tokens">Token-change volume</option>
          </select>
        </label>
      </div>
      <p className="meta">
        Showing {filtered.length} of {rows.length} changed rows · Unchanged:{" "}
        {unchangedCount}
      </p>
      <div className="table-wrap">
        <table className="data">
          <thead>
            <tr>
              <th scope="col">Section</th>
              <th scope="col">Class</th>
              <th scope="col">Token Δ</th>
              <th scope="col">
                <span className="visually-hidden">Evidence</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((r) => {
              const delta = countTokenDelta(r.legal_text_ops);
              return (
                <tr key={`${r.section_id}-${r.relationship}`}>
                  <td>
                    § {r.section_num_b || r.section_num_a || "—"}
                    <div className="meta">{r.heading || r.section_id}</div>
                  </td>
                  <td>
                    <span className="pill">{relationshipLabel(r.relationship)}</span>
                  </td>
                  <td className="meta">
                    +{delta.additions} / −{delta.deletions}
                  </td>
                  <td>
                    <Link href={r.href}>View comparison evidence</Link>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
