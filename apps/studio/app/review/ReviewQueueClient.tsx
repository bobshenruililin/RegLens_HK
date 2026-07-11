"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

type Item = {
  decision_id: string;
  decision_title: string;
  regulator_code: string;
  proposition: {
    id: string;
    prop_type: string;
    epistemic_class: string;
    claim_text: string;
    confidence: number;
    evidence: Array<{ page_no: number; quote: string }>;
  };
};

/** Demo-mode review queue (file seed via /api/review). */
export default function ReviewQueueClient() {
  const [items, setItems] = useState<Item[]>([]);
  const [message, setMessage] = useState<string | null>(null);

  async function refresh() {
    const res = await fetch("/api/review");
    const data = await res.json();
    setItems(data.items || []);
  }

  useEffect(() => {
    refresh();
  }, []);

  async function act(item: Item, review_status: "accepted" | "rejected") {
    setMessage(null);
    const res = await fetch("/api/review", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        decision_id: item.decision_id,
        proposition_id: item.proposition.id,
        review_status,
      }),
    });
    const data = await res.json();
    if (!res.ok) {
      setMessage(data.error || "Review failed");
      return;
    }
    setMessage(`${review_status}: ${item.proposition.prop_type}`);
    await refresh();
  }

  return (
    <section className="panel">
      <h1>Review queue</h1>
      <p>
        No proposition is published without supporting source spans and an
        accept/edit decision. Demo mode uses local seed.
      </p>
      {message && <p className="warning">{message}</p>}
      {items.length === 0 && <p>Queue empty.</p>}
      <div className="prop-list">
        {items.map((item) => (
          <div className="prop" key={item.proposition.id}>
            <div className="prop-type">
              {item.regulator_code} · {item.proposition.prop_type} ·{" "}
              {item.proposition.epistemic_class}
            </div>
            <p className="claim">{item.proposition.claim_text}</p>
            <p>
              <Link href={`/decisions/${item.decision_id}`}>
                {item.decision_title}
              </Link>
              {" · "}
              <Link href={`/review/${item.decision_id}`}>Two-column review</Link>
            </p>
            <ul>
              {item.proposition.evidence.map((ev, i) => (
                <li key={i}>
                  page {ev.page_no}: “{ev.quote}”
                </li>
              ))}
            </ul>
            <button type="button" onClick={() => act(item, "accepted")}>
              Accept & publish
            </button>{" "}
            <button type="button" onClick={() => act(item, "rejected")}>
              Reject
            </button>
          </div>
        ))}
      </div>
    </section>
  );
}
