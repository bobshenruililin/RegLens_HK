"use client";

import { useId, useState } from "react";
import { RedlineView, StatuteText } from "@/components/RedlineView";
import {
  countTokenDelta,
  summarizeMetadataOps,
  summarizeRelationship,
  summarizeStructuralOps,
  type Op,
} from "@/lib/ops";

type Props = {
  highlightLegalText: string[];
  plainTextA: string;
  plainTextB: string;
  metadataOps: Op[] | unknown;
  structuralOps: Op[] | unknown;
  relationship: string;
  numA?: string | null;
  numB?: string | null;
  headingA?: string | null;
  headingB?: string | null;
  view?: "inline" | "side";
};

export function ComparePanels({
  highlightLegalText,
  plainTextA,
  plainTextB,
  metadataOps,
  structuralOps,
  relationship,
  numA,
  numB,
  headingA,
  headingB,
  view = "inline",
}: Props) {
  const baseId = useId();
  const [tab, setTab] = useState<"text" | "structure" | "status" | "tech">(
    "text",
  );
  const meta = (metadataOps as Op[]) || [];
  const struct = (structuralOps as Op[]) || [];
  const tokens = countTokenDelta(
    relationship === "status_changed" ? [] : (([] as Op[]).concat(
      // approximate from highlight only when ops not counted separately
    )),
  );
  void tokens;
  const legalDelta = countTokenDelta(
    // Prefer ops if present via highlight length fallback handled in parent
    meta,
  );
  void legalDelta;

  const tabs: Array<{ id: typeof tab; label: string }> = [
    { id: "text", label: "Legal text" },
    { id: "structure", label: "Structure" },
    { id: "status", label: "Status / metadata" },
    { id: "tech", label: "Technical record" },
  ];

  const relLines = summarizeRelationship(relationship, {
    numA,
    numB,
    headingChanged: Boolean(headingA && headingB && headingA !== headingB),
  });

  return (
    <div>
      <ul className="plain-list">
        {relLines.map((l) => (
          <li key={l}>{l}</li>
        ))}
      </ul>

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
            onKeyDown={(e) => {
              const idx = tabs.findIndex((x) => x.id === tab);
              if (e.key === "ArrowRight") {
                e.preventDefault();
                setTab(tabs[(idx + 1) % tabs.length].id);
              } else if (e.key === "ArrowLeft") {
                e.preventDefault();
                setTab(tabs[(idx - 1 + tabs.length) % tabs.length].id);
              }
            }}
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
        {relationship === "status_changed" ? (
          <p className="meta">
            This transition is classified as status-only. Legal-text tokens are
            unchanged; see Status / metadata.
          </p>
        ) : null}
        {view === "inline" ? (
          <>
            <h2 className="section-title">Inline redline</h2>
            <RedlineView lines={highlightLegalText} />
          </>
        ) : null}
        <h2 className="section-title">Side-by-side canonical text</h2>
        <div className="side-by-side side-by-side-stack-mobile" style={{ marginTop: "0.75rem" }}>
          <div>
            <h3>Snapshot A</h3>
            <StatuteText text={plainTextA} />
          </div>
          <div>
            <h3>Snapshot B</h3>
            <StatuteText text={plainTextB} />
          </div>
        </div>
      </div>

      <div
        role="tabpanel"
        id={`${baseId}-panel-structure`}
        aria-labelledby={`${baseId}-structure`}
        hidden={tab !== "structure"}
      >
        <h2 className="section-title">Structure</h2>
        <ul className="plain-list">
          {summarizeStructuralOps(struct).map((l) => (
            <li key={l}>{l}</li>
          ))}
        </ul>
      </div>

      <div
        role="tabpanel"
        id={`${baseId}-panel-status`}
        aria-labelledby={`${baseId}-status`}
        hidden={tab !== "status"}
      >
        <h2 className="section-title">Status / metadata</h2>
        <ul className="plain-list">
          {summarizeMetadataOps(meta).map((l) => (
            <li key={l}>{l}</li>
          ))}
        </ul>
        <p className="meta">
          Status-only changes are listed here and are not presented as textual
          amendments.
        </p>
      </div>

      <div
        role="tabpanel"
        id={`${baseId}-panel-tech`}
        aria-labelledby={`${baseId}-tech`}
        hidden={tab !== "tech"}
      >
        <details>
          <summary>Technical record (raw deterministic operations)</summary>
          <h3>Metadata ops</h3>
          <pre className="redline">{JSON.stringify(meta, null, 2)}</pre>
          <h3>Structural ops</h3>
          <pre className="redline">{JSON.stringify(struct, null, 2)}</pre>
        </details>
      </div>
    </div>
  );
}
