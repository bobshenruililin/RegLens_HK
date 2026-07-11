"use client";

import { FormEvent, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

export default function LoginClient() {
  const router = useRouter();
  const params = useSearchParams();
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    const res = await fetch("/api/login", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ password, username: "reviewer" }),
    });
    if (!res.ok) {
      setError("Invalid password");
      return;
    }
    router.push(params.get("next") || "/");
    router.refresh();
  }

  return (
    <section className="panel" style={{ maxWidth: 420 }}>
      <h1>Sign in</h1>
      <p>
        Internal research access only. Default local password is{" "}
        <code>reglens-internal</code> (override with <code>AUTH_PASSWORD</code>).
      </p>
      <form onSubmit={onSubmit}>
        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={{
              display: "block",
              width: "100%",
              margin: "0.4rem 0 1rem",
              padding: "0.5rem",
            }}
          />
        </label>
        {error && <p className="warning">{error}</p>}
        <button type="submit">Continue</button>
      </form>
    </section>
  );
}
