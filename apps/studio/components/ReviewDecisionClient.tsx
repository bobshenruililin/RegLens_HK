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
  evidence: Array<{ page_no: number; quote_text: string }>;
};

type Bundle = {
  decision: {
    id: string;
    title: string | null;
    external_ref: string;
    regulator_code: string;
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
  prop_type: string;
  epistemic_class: string;
  claim_text: string;
  review_status: string;
  evidence: Array<{ page_no: number; quote: string }>;
};

export function ReviewDecisionClient({
  decisionId,
  mode,
  demo,
  postgres,
}: {
  decisionId: string;
  mode: string;
  demo?: {
    title: string;
    regulator: string;
    pages: Array<{ page_no: number; text: string; span_id: string }>;
    propositions: DemoProp[];
  } | null;
  postgres?: Bundle | null;
}) {
  const router = useRouter();
  const [message, setMessage] = useState<string | null>(null);
  const [csrf, setCsrf] = useState<string | null>(null);
  const [edits, setEdits] = useState<Record<string, string>>({});

  useEffect(() => {
    if (mode !== "postgres") return;
    fetch("/api/csrf")
      .then((r) => r.json())
      .then((d) => setCsrf(d.csrf || null))
      .catch(() => undefined);
  }, [mode]);

  async function actPostgres(prop: PropRow, review_status: "accepted" | "rejected") {
    setMessage(null);
    const claim = edits[prop.extracted_proposition_id];
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
  }

  async function actDemo(prop: DemoProp, review_status: "accepted" | "rejected") {
    setMessage(null);
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
  }

  if (mode === "demo" && demo) {
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
          {message && <p className="warning">{message}</p>}
          <div className="prop-list">
            {demo.propositions.map((prop) => (
              <div className="prop" key={prop.id}>
                <div className="prop-type">
                  {prop.prop_type} · {prop.epistemic_class} · {prop.review_status}
                </div>
                <textarea
                  value={edits[prop.id] ?? prop.claim_text}
                  onChange={(e) =>
                    setEdits((s) => ({ ...s, [prop.id]: e.target.value }))
                  }
                  rows={3}
                  style={{ width: "100%", margin: "0.4rem 0" }}
                />
                <ul>
                  {prop.evidence.map((ev, i) => (
                    <li key={i}>
                      page {ev.page_no}: “{ev.quote}”
                    </li>
                  ))}
                </ul>
                <button type="button" onClick={() => actDemo(prop, "accepted")}>
                  Accept
                </button>{" "}
                <button type="button" onClick={() => actDemo(prop, "rejected")}>
                  Reject
                </button>
              </div>
            ))}
          </div>
          <p>
            <Link href={`/decisions/${decisionId}`}>Decision view</Link>
          </p>
        </section>
      </div>
    );
  }

  if (mode === "postgres" && postgres) {
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
          {message && <p className="warning">{message}</p>}
          <div className="prop-list">
            {postgres.propositions.map((prop) => (
              <div className="prop" key={prop.revision_id}>
                <div className="prop-type">
                  {prop.prop_type} · {prop.client_ref} · rev {prop.revision_number} ·{" "}
                  {prop.latest_review_status || "none"}
                </div>
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
                  rows={3}
                  style={{ width: "100%", margin: "0.4rem 0" }}
                />
                <ul>
                  {prop.evidence.map((ev, i) => (
                    <li key={i}>
                      page {ev.page_no}: “{ev.quote_text}”
                    </li>
                  ))}
                </ul>
                <button
                  type="button"
                  onClick={() => actPostgres(prop, "accepted")}
                >
                  Accept
                </button>{" "}
                <button
                  type="button"
                  onClick={() => actPostgres(prop, "rejected")}
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
