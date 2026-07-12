"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { StatusNotice } from "@/components/StatusNotice";

type Pair = {
  id: string;
  instrument: string;
  from: string;
  to: string;
  section_id: string;
  relationship: string;
  heading?: string;
};

type Decision = "CONFIRM" | "REJECT" | "UNCERTAIN" | "";

/**
 * Private audit workspace. Enabled only when NEXT_PUBLIC_LAWTRACE_AUDIT=1.
 * Decisions stay in browser localStorage until exported; they are never written
 * back into source/web artifacts automatically.
 */
export default function AuditClient({ pairs }: { pairs: Pair[] }) {
  const storageKey = "lawtrace-audit-v1";
  const [notes, setNotes] = useState<Record<string, { decision: Decision; note: string }>>(
    () => {
      if (typeof window === "undefined") return {};
      try {
        return JSON.parse(localStorage.getItem(storageKey) || "{}");
      } catch {
        return {};
      }
    },
  );

  const stratified = useMemo(() => pairs, [pairs]);

  function setDecision(id: string, decision: Decision) {
    setNotes((prev) => {
      const next: Record<string, { decision: Decision; note: string }> = {
        ...prev,
        [id]: { decision, note: prev[id]?.note || "" },
      };
      localStorage.setItem(storageKey, JSON.stringify(next));
      return next;
    });
  }

  function setNote(id: string, note: string) {
    setNotes((prev) => {
      const next: Record<string, { decision: Decision; note: string }> = {
        ...prev,
        [id]: { decision: (prev[id]?.decision || "") as Decision, note },
      };
      localStorage.setItem(storageKey, JSON.stringify(next));
      return next;
    });
  }

  function exportJson() {
    const payload = {
      exported_at: new Date().toISOString(),
      note: "Local audit export only. Not imported as human-confirmed gold.",
      reviews: stratified.map((p) => ({
        ...p,
        decision: notes[p.id]?.decision || "",
        reviewer_note: notes[p.id]?.note || "",
      })),
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "lawtrace-audit-export.json";
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <>
      <h1 className="page-title">Private audit workspace</h1>
      <StatusNotice compact />
      <p className="meta">
        {stratified.length} deterministically selected changed pairs. Decisions
        remain local until you export. This UI does not mark source artifacts as
        human-confirmed.
      </p>
      <p>
        <button type="button" className="btn" onClick={exportJson}>
          Export review JSON
        </button>
      </p>
      <div className="table-wrap" style={{ marginTop: "1rem" }}>
        <table className="data">
          <thead>
            <tr>
              <th>#</th>
              <th>Pair</th>
              <th>Decision</th>
              <th>Note</th>
            </tr>
          </thead>
          <tbody>
            {stratified.map((p, idx) => (
              <tr key={p.id}>
                <td>{idx + 1}</td>
                <td>
                  <div className="meta">{p.instrument}</div>
                  <div>
                    {p.relationship} · § {p.heading || "—"}
                  </div>
                  <div className="meta">
                    <code>{p.section_id}</code>
                  </div>
                  <Link
                    href={`/instruments/${p.instrument}/sections/${encodeURIComponent(p.section_id)}/compare/${encodeURIComponent(p.from)}/${encodeURIComponent(p.to)}/`}
                  >
                    Open comparison
                  </Link>
                </td>
                <td>
                  {(["CONFIRM", "REJECT", "UNCERTAIN"] as Decision[]).map((d) => (
                    <label key={d} style={{ display: "block" }}>
                      <input
                        type="radio"
                        name={`d-${p.id}`}
                        checked={(notes[p.id]?.decision || "") === d}
                        onChange={() => setDecision(p.id, d)}
                      />{" "}
                      {d}
                    </label>
                  ))}
                </td>
                <td>
                  <textarea
                    rows={3}
                    style={{ width: "100%" }}
                    value={notes[p.id]?.note || ""}
                    onChange={(e) => setNote(p.id, e.target.value)}
                    aria-label={`Reviewer note for ${p.id}`}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
