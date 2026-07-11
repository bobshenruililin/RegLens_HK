"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";

type Hit = {
  decision_id: string;
  title: string;
  regulator_code: string;
  profession?: string;
  prop_type?: string;
  claim_text?: string;
  page_no?: number | null;
  score: number;
};

export default function SearchPage() {
  const [q, setQ] = useState("misconduct");
  const [regulator, setRegulator] = useState("");
  const [hits, setHits] = useState<Hit[]>([]);
  const [notice, setNotice] = useState("");

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    const params = new URLSearchParams({ q });
    if (regulator) params.set("regulator", regulator);
    const res = await fetch(`/api/search?${params.toString()}`);
    const data = await res.json();
    setHits(data.hits || []);
    setNotice(data.notice || "");
  }

  return (
    <section className="panel">
      <h1>Search</h1>
      <p>Keyword full-text search over published propositions only.</p>
      <form onSubmit={onSubmit} style={{ display: "grid", gap: "0.75rem", maxWidth: 640 }}>
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Keywords"
          style={{ padding: "0.55rem" }}
        />
        <select value={regulator} onChange={(e) => setRegulator(e.target.value)}>
          <option value="">All regulators</option>
          <option value="MCHK">MCHK</option>
          <option value="DCHK">DCHK</option>
        </select>
        <button type="submit">Search</button>
      </form>
      {notice && <p className="warning">{notice}</p>}
      <div className="prop-list" style={{ marginTop: "1rem" }}>
        {hits.map((hit, idx) => (
          <div className="prop" key={`${hit.decision_id}-${idx}`}>
            <div className="prop-type">
              {hit.regulator_code}
              {hit.prop_type ? ` · ${hit.prop_type}` : ""}
              {hit.page_no ? ` · page ${hit.page_no}` : ""}
            </div>
            <p className="claim">{hit.claim_text || hit.title}</p>
            <Link
              href={`/decisions/${hit.decision_id}${hit.page_no ? `#page-${hit.page_no}` : ""}`}
            >
              Open decision
            </Link>
          </div>
        ))}
      </div>
    </section>
  );
}
