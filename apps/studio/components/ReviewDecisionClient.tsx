"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

type PropRow = {
  extracted_proposition_id: string;
  client_ref: string;
  prop_type: string;
  epistemic_class: string;
  claim_text: string;
  revision_id: string;
  revision_number: number;
  latest_review_status: string | null;
  structured_json?: unknown;
  critic_result?: unknown;
  evidence: Array<{ page_no: number; quote_text: string; text_variant?: string | null }>;
};

type Bundle = {
  decision: {
    id: string;
    title: string | null;
    external_ref: string;
    regulator_code: string;
    source_id?: string | null;
  };
  spans: Array<{
    id: string;
    page_no: number;
    text: string;
    stable_span_id: string;
  }>;
  propositions: PropRow[];
};

type DemoProp = {
  id: string;
  client_ref?: string;
  prop_type: string;
  epistemic_class: string;
  claim_text: string;
  review_status: string;
  critic_result?: unknown;
  evidence: Array<{ page_no: number; quote: string; text_variant?: string | null }>;
};

type ChecklistItem = {
  key: string;
  label: string;
  complete: boolean;
  hint: string;
};

function textFromUnknown(value: unknown): string | null {
  if (value == null) return null;
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  if (Array.isArray(value)) {
    const parts = value.map(textFromUnknown).filter(Boolean);
    return parts.length ? parts.join(", ") : null;
  }
  if (typeof value === "object") {
    const record = value as Record<string, unknown>;
    const result = textFromUnknown(record.result);
    const reasons = textFromUnknown(record.reasons);
    if (result && reasons) return `${result} (${reasons})`;
    if (result) return result;
    return JSON.stringify(record);
  }
  return null;
}

function evidenceVariantLabel(value?: string | null): string | null {
  if (!value) return null;
  const normalized = value.toLowerCase().replace(/[_-]/g, " ");
  if (normalized.includes("ocr")) return "OCR text";
  if (normalized.includes("source")) return "Source text";
  return value;
}

function hasPropType(
  propositions: Array<{ prop_type: string; claim_text: string; evidence: Array<{ quote?: string; quote_text?: string }> }>,
  types: string[]
): boolean {
  return propositions.some((prop) => types.includes(prop.prop_type));
}

function privacyReviewed(
  propositions: Array<{ claim_text: string }>
): boolean {
  const sensitivePatterns = [
    /\bPatient\s+[A-Z]\b/i,
    /\bReg\.?\s*No\.?:?\s*[A-Z]?\d{3,}\b/i,
  ];
  return propositions.every((prop) =>
    sensitivePatterns.every((pattern) => !pattern.test(prop.claim_text))
  );
}

function ChecklistPanel({ items }: { items: ChecklistItem[] }) {
  return (
    <aside className="checklist" aria-label="Decision completeness checklist">
      <h2>Completeness checklist</h2>
      <ul>
        {items.map((item) => (
          <li key={item.key}>
            <span
              className={`badge ${item.complete ? "badge-ok" : "badge-warn"}`}
              aria-label={item.complete ? "Complete" : "Needs review"}
            >
              {item.complete ? "OK" : "Review"}
            </span>
            <strong>{item.label}</strong>
            <span>{item.hint}</span>
          </li>
        ))}
      </ul>
    </aside>
  );
}

export function ReviewDecisionClient({
  decisionId,
  mode,
  previousDecisionId,
  nextDecisionId,
  demo,
  postgres,
}: {
  decisionId: string;
  mode: string;
  previousDecisionId?: string | null;
  nextDecisionId?: string | null;
  demo?: {
    title: string;
    regulator: string;
    external_ref?: string | null;
    source_id?: string | null;
    licence_notice?: string;
    defendant_name_as_published?: string | null;
    pages: Array<{ page_no: number; text: string; span_id: string }>;
    propositions: DemoProp[];
  } | null;
  postgres?: Bundle | null;
}) {
  const router = useRouter();
  const [message, setMessage] = useState<string | null>(null);
  const [csrf, setCsrf] = useState<string | null>(null);
  const [edits, setEdits] = useState<Record<string, string>>({});
  const [busyId, setBusyId] = useState<string | null>(null);

  useEffect(() => {
    if (mode !== "postgres") return;
    fetch("/api/csrf")
      .then((r) => r.json())
      .then((d) => setCsrf(d.csrf || null))
      .catch(() => undefined);
  }, [mode]);

  async function actPostgres(prop: PropRow, review_status: "accepted" | "rejected") {
    setMessage(null);
    setBusyId(prop.extracted_proposition_id);
    const claim = edits[prop.extracted_proposition_id];
    try {
      const res = await fetch("/api/pg/review", {
        method: "POST",
        headers: {
          "content-type": "application/json",
          ...(csrf ? { "x-csrf-token": csrf } : {}),
        },
        body: JSON.stringify({
          extracted_proposition_id: prop.extracted_proposition_id,
          review_status,
          expected_head_revision_number: prop.revision_number,
          claim_text: claim,
          csrf,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        setMessage(data.error || "Review failed");
        return;
      }
      setMessage(`${data.status || review_status}: ${prop.prop_type}`);
      router.refresh();
    } finally {
      setBusyId(null);
    }
  }

  async function actDemo(prop: DemoProp, review_status: "accepted" | "rejected") {
    setMessage(null);
    setBusyId(prop.id);
    try {
      const res = await fetch("/api/review", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          decision_id: decisionId,
          proposition_id: prop.id,
          review_status,
          claim_text: edits[prop.id],
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        setMessage(data.error || "Review failed");
        return;
      }
      setMessage(`${review_status}: ${prop.prop_type}`);
      router.refresh();
    } finally {
      setBusyId(null);
    }
  }

  if (mode === "demo" && demo) {
    const checklist = [
      {
        key: "metadata",
        label: "Metadata",
        complete: Boolean(demo.title && demo.regulator && demo.external_ref),
        hint: demo.external_ref || "External reference missing",
      },
      {
        key: "charges",
        label: "Charges",
        complete: hasPropType(demo.propositions, ["charge"]),
        hint: "At least one charge proposition",
      },
      {
        key: "findings",
        label: "Findings",
        complete: hasPropType(demo.propositions, ["finding"]),
        hint: "Finding outcome captured",
      },
      {
        key: "sanction",
        label: "Sanction",
        complete: hasPropType(demo.propositions, ["sanction", "costs"]),
        hint: "Order/costs captured",
      },
      {
        key: "factors",
        label: "Factors",
        complete: hasPropType(demo.propositions, ["aggravating_factor", "mitigating_factor"]),
        hint: "Aggravating or mitigating factor captured",
      },
      {
        key: "rules",
        label: "Rules",
        complete: hasPropType(demo.propositions, ["rule", "legal_test"]),
        hint: "Rule or legal test captured",
      },
      {
        key: "authorities",
        label: "Authorities",
        complete: hasPropType(demo.propositions, ["authority"]),
        hint: "Cited authority captured where present",
      },
      {
        key: "attribution",
        label: "Attribution",
        complete: Boolean(demo.source_id || demo.licence_notice || demo.external_ref),
        hint: demo.source_id || demo.licence_notice || "Source attribution missing",
      },
      {
        key: "privacy",
        label: "Privacy",
        complete: privacyReviewed(demo.propositions),
        hint: "Published claims avoid obvious patient/registration identifiers",
      },
    ];
    return (
      <div className="review-grid">
        <section className="panel">
          <h2>Evidence</h2>
          {demo.pages.map((page) => (
            <div className="page-block" key={page.span_id} id={`page-${page.page_no}`}>
              <strong>Page {page.page_no}</strong>
              <pre>{page.text}</pre>
            </div>
          ))}
        </section>
        <section className="panel">
          <h1>Review</h1>
          <p>
            {demo.regulator} · {demo.title}
          </p>
          <nav className="review-nav" aria-label="Decision review navigation">
            {previousDecisionId ? (
              <Link href={`/review/${previousDecisionId}`} aria-label="Open previous decision">
                Previous
              </Link>
            ) : (
              <span aria-disabled="true">Previous</span>
            )}
            <Link href={`/decisions/${decisionId}`}>Decision view</Link>
            {nextDecisionId ? (
              <Link href={`/review/${nextDecisionId}`} aria-label="Open next decision">
                Next
              </Link>
            ) : (
              <span aria-disabled="true">Next</span>
            )}
          </nav>
          <ChecklistPanel items={checklist} />
          {message && (
            <p className="warning" role="status" aria-live="polite">
              {message}
            </p>
          )}
          <div className="prop-list">
            {demo.propositions.map((prop) => (
              <div className="prop" key={prop.id}>
                <div className="prop-type">
                  {prop.prop_type} · {prop.client_ref || prop.id} ·{" "}
                  {prop.epistemic_class} · {prop.review_status}
                </div>
                {textFromUnknown(prop.critic_result) && (
                  <p>
                    <span className="badge">Critic</span>
                    {textFromUnknown(prop.critic_result)}
                  </p>
                )}
                <textarea
                  value={edits[prop.id] ?? prop.claim_text}
                  onChange={(e) =>
                    setEdits((s) => ({ ...s, [prop.id]: e.target.value }))
                  }
                  aria-label={`Claim text for ${prop.prop_type}`}
                  rows={3}
                  style={{ width: "100%", margin: "0.4rem 0" }}
                />
                <ul>
                  {prop.evidence.map((ev, i) => (
                    <li key={i}>
                      {evidenceVariantLabel(ev.text_variant) && (
                        <span className="badge">
                          {evidenceVariantLabel(ev.text_variant)}
                        </span>
                      )}
                      page {ev.page_no}: “{ev.quote}”
                    </li>
                  ))}
                </ul>
                <button
                  type="button"
                  onClick={() => actDemo(prop, "accepted")}
                  disabled={busyId === prop.id}
                  aria-label={`Accept ${prop.prop_type} proposition`}
                >
                  Accept
                </button>{" "}
                <button
                  type="button"
                  onClick={() => actDemo(prop, "rejected")}
                  disabled={busyId === prop.id}
                  aria-label={`Reject ${prop.prop_type} proposition`}
                >
                  Reject
                </button>
              </div>
            ))}
          </div>
        </section>
      </div>
    );
  }

  if (mode === "postgres" && postgres) {
    const checklist = [
      {
        key: "metadata",
        label: "Metadata",
        complete: Boolean(
          postgres.decision.regulator_code &&
            postgres.decision.external_ref &&
            (postgres.decision.title || postgres.decision.id)
        ),
        hint: postgres.decision.external_ref,
      },
      {
        key: "charges",
        label: "Charges",
        complete: hasPropType(postgres.propositions, ["charge"]),
        hint: "At least one charge proposition",
      },
      {
        key: "findings",
        label: "Findings",
        complete: hasPropType(postgres.propositions, ["finding"]),
        hint: "Finding outcome captured",
      },
      {
        key: "sanction",
        label: "Sanction",
        complete: hasPropType(postgres.propositions, ["sanction", "costs"]),
        hint: "Order/costs captured",
      },
      {
        key: "factors",
        label: "Factors",
        complete: hasPropType(postgres.propositions, [
          "aggravating_factor",
          "mitigating_factor",
        ]),
        hint: "Aggravating or mitigating factor captured",
      },
      {
        key: "rules",
        label: "Rules",
        complete: hasPropType(postgres.propositions, ["rule", "legal_test"]),
        hint: "Rule or legal test captured",
      },
      {
        key: "authorities",
        label: "Authorities",
        complete: hasPropType(postgres.propositions, ["authority"]),
        hint: "Cited authority captured where present",
      },
      {
        key: "attribution",
        label: "Attribution",
        complete: Boolean(postgres.decision.source_id || postgres.decision.external_ref),
        hint: postgres.decision.source_id || postgres.decision.external_ref,
      },
      {
        key: "privacy",
        label: "Privacy",
        complete: privacyReviewed(postgres.propositions),
        hint: "Published claims avoid obvious patient/registration identifiers",
      },
    ];
    return (
      <div className="review-grid">
        <section className="panel">
          <h2>Evidence</h2>
          {postgres.spans.length === 0 && <p>No spans linked.</p>}
          {postgres.spans.map((span) => (
            <div className="page-block" key={span.id} id={`page-${span.page_no}`}>
              <strong>
                Page {span.page_no}{" "}
                <span className="badge">{span.stable_span_id.slice(0, 8)}</span>
              </strong>
              <pre>{span.text}</pre>
            </div>
          ))}
        </section>
        <section className="panel">
          <h1>Review</h1>
          <p>
            {postgres.decision.regulator_code} ·{" "}
            {postgres.decision.title || postgres.decision.external_ref}
          </p>
          <nav className="review-nav" aria-label="Decision review navigation">
            {previousDecisionId ? (
              <Link href={`/review/${previousDecisionId}`} aria-label="Open previous decision">
                Previous
              </Link>
            ) : (
              <span aria-disabled="true">Previous</span>
            )}
            <Link href={`/decisions/${decisionId}`}>Decision view</Link>
            {nextDecisionId ? (
              <Link href={`/review/${nextDecisionId}`} aria-label="Open next decision">
                Next
              </Link>
            ) : (
              <span aria-disabled="true">Next</span>
            )}
          </nav>
          <ChecklistPanel items={checklist} />
          {message && (
            <p className="warning" role="status" aria-live="polite">
              {message}
            </p>
          )}
          <div className="prop-list">
            {postgres.propositions.map((prop) => (
              <div className="prop" key={prop.revision_id}>
                <div className="prop-type">
                  {prop.prop_type} · {prop.client_ref} · rev {prop.revision_number} ·{" "}
                  {prop.latest_review_status || "none"}
                </div>
                {textFromUnknown(prop.critic_result) && (
                  <p>
                    <span className="badge">Critic</span>
                    {textFromUnknown(prop.critic_result)}
                  </p>
                )}
                <textarea
                  value={
                    edits[prop.extracted_proposition_id] ?? prop.claim_text
                  }
                  onChange={(e) =>
                    setEdits((s) => ({
                      ...s,
                      [prop.extracted_proposition_id]: e.target.value,
                    }))
                  }
                  aria-label={`Claim text for ${prop.client_ref}`}
                  rows={3}
                  style={{ width: "100%", margin: "0.4rem 0" }}
                />
                <ul>
                  {prop.evidence.map((ev, i) => (
                    <li key={i}>
                      {evidenceVariantLabel(ev.text_variant) && (
                        <span className="badge">
                          {evidenceVariantLabel(ev.text_variant)}
                        </span>
                      )}
                      page {ev.page_no}: “{ev.quote_text}”
                    </li>
                  ))}
                </ul>
                <button
                  type="button"
                  onClick={() => actPostgres(prop, "accepted")}
                  disabled={busyId === prop.extracted_proposition_id}
                  aria-label={`Accept ${prop.client_ref}`}
                >
                  Accept
                </button>{" "}
                <button
                  type="button"
                  onClick={() => actPostgres(prop, "rejected")}
                  disabled={busyId === prop.extracted_proposition_id}
                  aria-label={`Reject ${prop.client_ref}`}
                >
                  Reject
                </button>
              </div>
            ))}
          </div>
        </section>
      </div>
    );
  }

  return (
    <section className="panel">
      <h1>Review</h1>
      <p className="warning">Decision not found.</p>
      <form
        onSubmit={(e: FormEvent) => {
          e.preventDefault();
        }}
      />
    </section>
  );
}
