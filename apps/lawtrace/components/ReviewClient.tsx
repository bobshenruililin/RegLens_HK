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
 * Local review workspace — opt-in build only (LAWTRACE_LOCAL_REVIEW=1).
 * Not authentication. Decisions stay in browser localStorage until exported.
 * Reviewer-entered status is distinct from algorithmic relationship labels.
 */
export default function ReviewClient({ pairs }: { pairs: Pair[] }) {
  const storageKey = "lawtrace-local-review-v1";
  const [notes, setNotes] = useState<
    Record<string, { decision: Decision; note: string }>
  >(() => {
    if (typeof window === "undefined") return {};
    try {
      return JSON.parse(localStorage.getItem(storageKey) || "{}");
    } catch {
      return {};
    }
  });

  const stratified = useMemo(() => pairs, [pairs]);

  function setDecision(id: string, decision: Decision) {
    setNotes((prev) => {
      const next = {
        ...prev,
        [id]: { decision, note: prev[id]?.note || "" },
      };
      localStorage.setItem(storageKey, JSON.stringify(next));
      return next;
    });
  }

  function setNote(id: string, note: string) {
    setNotes((prev) => {
      const next = {
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
      workspace: "local_review",
      note:
        "Local review export only. Reviewer-entered decision is distinct from algorithmic relationship labels. Not imported as human-confirmed gold.",
      reviews: stratified.map((p) => ({
        ...p,
        algorithmic_relationship: p.relationship,
        reviewer_decision: notes[p.id]?.decision || "",
        reviewer_note: notes[p.id]?.note || "",
      })),
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "lawtrace-local-review-export.json";
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <>
      <h1 className="page-title">Local review workspace</h1>
      <StatusNotice compact />
      <p className="meta">
        {stratified.length} deterministically selected changed pairs. This is a
        local development aid — not access control and not a public review
        service. Reviewer decisions remain in this browser until exported.
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
              <th scope="col">#</th>
              <th scope="col">Pair</th>
              <th scope="col">Reviewer decision</th>
              <th scope="col">Note</th>
            </tr>
          </thead>
          <tbody>
            {stratified.map((p, idx) => (
              <tr key={p.id}>
                <td>{idx + 1}</td>
                <td>
                  <div className="meta">{p.instrument}</div>
                  <div>
                    Algorithmic class: {p.relationship} · § {p.heading || "—"}
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
