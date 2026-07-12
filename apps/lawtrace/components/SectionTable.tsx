"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { sectionSortKey } from "@/lib/format";

type Row = {
  section_id: string;
  latest_num?: string;
  latest_heading?: string;
  descriptive_change_count: number;
  nums_seen: string[];
  headings_seen: string[];
};

export function SectionTable({
  instrumentId,
  sections,
}: {
  instrumentId: string;
  sections: Row[];
}) {
  const [q, setQ] = useState("");
  const [filter, setFilter] = useState<"all" | "changed" | "stable">("all");

  const rows = useMemo(() => {
    return sections
      .filter((s) => {
        if (filter === "changed" && !(s.descriptive_change_count > 0)) return false;
        if (filter === "stable" && s.descriptive_change_count > 0) return false;
        const hay = [
          s.section_id,
          s.latest_num,
          s.latest_heading,
          ...(s.nums_seen || []),
          ...(s.headings_seen || []),
        ]
          .join(" ")
          .toLowerCase();
        return !q || hay.includes(q.toLowerCase());
      })
      .sort((a, b) =>
        sectionSortKey(a.latest_num || a.nums_seen[0]).localeCompare(
          sectionSortKey(b.latest_num || b.nums_seen[0]),
        ),
      );
  }, [sections, q, filter]);

  return (
    <div>
      <div className="toolbar">
        <input
          type="search"
          placeholder="Search sections"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          aria-label="Search sections"
        />
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value as typeof filter)}
          aria-label="Filter sections"
        >
          <option value="all">All</option>
          <option value="changed">Changed at least once</option>
          <option value="stable">No descriptive changes</option>
        </select>
      </div>
      <div className="table-wrap">
        <table className="data">
          <thead>
            <tr>
              <th>Section</th>
              <th>Heading</th>
              <th>Descriptive changes</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {rows.map((s) => (
              <tr key={s.section_id}>
                <td>§ {s.latest_num || s.nums_seen[0] || "—"}</td>
                <td>{s.latest_heading || s.headings_seen[0] || "—"}</td>
                <td>{s.descriptive_change_count}</td>
                <td>
                  <Link
                    href={`/instruments/${instrumentId}/sections/${encodeURIComponent(s.section_id)}/`}
                  >
                    History
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
