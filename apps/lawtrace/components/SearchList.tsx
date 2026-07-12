"use client";

import { useMemo, useState } from "react";
import Link from "next/link";

type Item = {
  href: string;
  title: string;
  subtitle?: string;
  haystack: string;
};

export function SearchList({
  items,
  placeholder,
}: {
  items: Item[];
  placeholder: string;
}) {
  const [q, setQ] = useState("");
  const filtered = useMemo(() => {
    const needle = q.trim().toLowerCase();
    if (!needle) return items.slice(0, 80);
    return items
      .filter((it) => it.haystack.toLowerCase().includes(needle))
      .slice(0, 80);
  }, [items, q]);

  return (
    <div>
      <div className="search">
        <label className="visually-hidden" htmlFor="lt-search">
          Search
        </label>
        <input
          id="lt-search"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder={placeholder}
          type="search"
        />
      </div>
      <div className="table-wrap">
        <table className="data">
          <thead>
            <tr>
              <th scope="col">Result</th>
              <th scope="col">Detail</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((it) => (
              <tr key={it.href}>
                <td>
                  <Link href={it.href}>{it.title}</Link>
                </td>
                <td className="muted">{it.subtitle}</td>
              </tr>
            ))}
            {!filtered.length ? (
              <tr>
                <td colSpan={2} className="muted">
                  No matches.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </div>
  );
}
