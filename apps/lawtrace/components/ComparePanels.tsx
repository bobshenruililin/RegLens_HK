"use client";

import { useId, useState } from "react";
import { RedlineView } from "@/components/RedlineView";

type Props = {
  highlightLegalText: string[];
  plainTextA: string;
  plainTextB: string;
  metadataOps: unknown;
  structuralOps: unknown;
  relationship: string;
};

export function ComparePanels({
  highlightLegalText,
  plainTextA,
  plainTextB,
  metadataOps,
  structuralOps,
  relationship,
}: Props) {
  const baseId = useId();
  const [tab, setTab] = useState<"text" | "structure" | "status">("text");
  const tabs: Array<{ id: typeof tab; label: string }> = [
    { id: "text", label: "Legal text" },
    { id: "structure", label: "Structure" },
    { id: "status", label: "Metadata / status" },
  ];

  return (
    <div>
      <div className="tablist" role="tablist" aria-label="Comparison channels">
        {tabs.map((t) => (
          <button
            key={t.id}
            type="button"
            role="tab"
            id={`${baseId}-${t.id}`}
            aria-selected={tab === t.id}
            aria-controls={`${baseId}-panel-${t.id}`}
            className={tab === t.id ? "tab active" : "tab"}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div
        role="tabpanel"
        id={`${baseId}-panel-text`}
        aria-labelledby={`${baseId}-text`}
        hidden={tab !== "text"}
      >
        <h2 className="section-title">Inline redline (legal-text channel)</h2>
        {relationship === "status_changed" ? (
          <p className="meta">
            This transition is classified as status-only. Legal-text tokens are
            unchanged; see the Metadata / status tab.
          </p>
        ) : null}
        <RedlineView lines={highlightLegalText} />
        <h2 className="section-title">Side-by-side canonical plain text</h2>
        <div className="side-by-side" style={{ marginTop: "0.75rem" }}>
          <div>
            <h3>Snapshot A</h3>
            <pre className="redline">{plainTextA}</pre>
          </div>
          <div>
            <h3>Snapshot B</h3>
            <pre className="redline">{plainTextB}</pre>
          </div>
        </div>
      </div>

      <div
        role="tabpanel"
        id={`${baseId}-panel-structure`}
        aria-labelledby={`${baseId}-structure`}
        hidden={tab !== "structure"}
      >
        <h2 className="section-title">Structural channel</h2>
        <pre className="redline">{JSON.stringify(structuralOps || [], null, 2)}</pre>
      </div>

      <div
        role="tabpanel"
        id={`${baseId}-panel-status`}
        aria-labelledby={`${baseId}-status`}
        hidden={tab !== "status"}
      >
        <h2 className="section-title">Metadata / status channel</h2>
        <pre className="redline">{JSON.stringify(metadataOps || [], null, 2)}</pre>
        <p className="meta">
          Status-only changes are listed here and are not presented as textual
          amendments.
        </p>
      </div>
    </div>
  );
}
