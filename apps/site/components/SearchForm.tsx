"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

type SearchFormProps = {
  initialQ?: string;
  initialRegulator?: string;
  initialProfession?: string;
  initialIssue?: string;
  initialSanction?: string;
  initialYear?: string;
  showFilters?: boolean;
  regulators?: string[];
  professions?: string[];
  issues?: string[];
  sanctions?: string[];
  years?: string[];
  actionLabel?: string;
};

export function SearchForm({
  initialQ = "",
  initialRegulator = "",
  initialProfession = "",
  initialIssue = "",
  initialSanction = "",
  initialYear = "",
  showFilters = false,
  regulators = ["MCHK", "DCHK"],
  professions = ["doctor", "dentist"],
  issues = [],
  sanctions = [],
  years = [],
  actionLabel = "Search",
}: SearchFormProps) {
  const router = useRouter();
  const [q, setQ] = useState(initialQ);
  const [regulator, setRegulator] = useState(initialRegulator);
  const [profession, setProfession] = useState(initialProfession);
  const [issue, setIssue] = useState(initialIssue);
  const [sanction, setSanction] = useState(initialSanction);
  const [year, setYear] = useState(initialYear);

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    const params = new URLSearchParams();
    if (q.trim()) params.set("q", q.trim());
    if (regulator) params.set("regulator", regulator);
    if (profession) params.set("profession", profession);
    if (issue) params.set("issue", issue);
    if (sanction) params.set("sanction", sanction);
    if (year) params.set("year", year);
    const qs = params.toString();
    router.push(qs ? `/explore/?${qs}` : "/explore/");
  }

  return (
    <form className="search-form" onSubmit={onSubmit} role="search">
      <div>
        <label htmlFor="search-q">Keyword and structured-field search</label>
        <div className="search-form__row">
          <input
            id="search-q"
            name="q"
            type="search"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Case ref, title, issue, sanction…"
            autoComplete="off"
          />
          <button className="btn" type="submit">
            {actionLabel}
          </button>
        </div>
        <p className="sr-only">
          Matches keywords against titles, case references, issues, sanctions, and
          other structured fields. This is not full-text or semantic search.
        </p>
      </div>

      {showFilters ? (
        <div className="search-form__filters">
          <div>
            <label htmlFor="filter-regulator">Regulator</label>
            <select
              id="filter-regulator"
              value={regulator}
              onChange={(e) => setRegulator(e.target.value)}
            >
              <option value="">Any</option>
              {regulators.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="filter-profession">Profession</label>
            <select
              id="filter-profession"
              value={profession}
              onChange={(e) => setProfession(e.target.value)}
            >
              <option value="">Any</option>
              {professions.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="filter-year">Year</label>
            <select
              id="filter-year"
              value={year}
              onChange={(e) => setYear(e.target.value)}
            >
              <option value="">Any</option>
              {years.map((y) => (
                <option key={y} value={y}>
                  {y}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="filter-issue">Issue</label>
            <select
              id="filter-issue"
              value={issue}
              onChange={(e) => setIssue(e.target.value)}
            >
              <option value="">Any</option>
              {issues.map((i) => (
                <option key={i} value={i}>
                  {i}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="filter-sanction">Sanction</label>
            <select
              id="filter-sanction"
              value={sanction}
              onChange={(e) => setSanction(e.target.value)}
            >
              <option value="">Any</option>
              {sanctions.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>
        </div>
      ) : null}
    </form>
  );
}
