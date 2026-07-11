"use client";

import { FormEvent, useMemo, useState } from "react";
import type { ResearchDecisionOption } from "../../lib/research-data";

type Props = {
  decisions: ResearchDecisionOption[];
};

function download(filename: string, content: string, type: string) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

export default function ResearchPackClient({ decisions }: Props) {
  const [selected, setSelected] = useState<string[]>(() =>
    decisions.slice(0, 3).map((decision) => decision.id)
  );
  const [markdown, setMarkdown] = useState("");
  const [csv, setCsv] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  const allSelected = useMemo(
    () => selected.length === decisions.length && decisions.length > 0,
    [decisions.length, selected.length]
  );

  function toggle(id: string) {
    setSelected((current) =>
      current.includes(id)
        ? current.filter((item) => item !== id)
        : [...current, id]
    );
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setMessage("");
    try {
      const res = await fetch("/api/research-pack", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ decision_ids: selected }),
      });
      const data = await res.json();
      if (!res.ok) {
        setMessage(data.error || "Research pack export failed");
        return;
      }
      setMarkdown(data.markdown || "");
      setCsv(data.csv || "");
      setMessage(`Prepared research pack for ${data.decision_count || 0} decisions.`);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={onSubmit} style={{ display: "grid", gap: "1rem" }}>
      <div>
        <button
          type="button"
          onClick={() =>
            setSelected(allSelected ? [] : decisions.map((decision) => decision.id))
          }
          aria-label={allSelected ? "Clear selected decisions" : "Select all decisions"}
        >
          {allSelected ? "Clear all" : "Select all"}
        </button>
      </div>
      <fieldset style={{ border: "1px solid var(--line)", padding: "1rem" }}>
        <legend>Decision ids</legend>
        {decisions.length === 0 && <p>No decisions available.</p>}
        <div className="prop-list">
          {decisions.map((decision) => (
            <label key={decision.id} className="prop" style={{ cursor: "pointer" }}>
              <input
                type="checkbox"
                checked={selected.includes(decision.id)}
                onChange={() => toggle(decision.id)}
              />{" "}
              <span className="prop-type">
                {decision.regulator_code} · {decision.external_ref}
              </span>
              <span className="claim" style={{ display: "block" }}>
                {decision.title}
              </span>
            </label>
          ))}
        </div>
      </fieldset>
      <div>
        <button type="submit" disabled={busy || selected.length === 0}>
          {busy ? "Preparing..." : "Prepare export"}
        </button>{" "}
        <button
          type="button"
          disabled={!markdown}
          onClick={() =>
            download("reglens-research-pack.md", markdown, "text/markdown;charset=utf-8")
          }
        >
          Download Markdown
        </button>{" "}
        <button
          type="button"
          disabled={!csv}
          onClick={() => download("reglens-research-pack.csv", csv, "text/csv;charset=utf-8")}
        >
          Download CSV
        </button>
      </div>
      {message && (
        <p className="warning" role="status" aria-live="polite">
          {message}
        </p>
      )}
      {markdown && (
        <details>
          <summary>Preview Markdown</summary>
          <textarea
            readOnly
            value={markdown}
            rows={14}
            style={{ width: "100%", marginTop: "0.75rem" }}
            aria-label="Research pack Markdown preview"
          />
        </details>
      )}
    </form>
  );
}
