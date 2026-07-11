"use client";

import { FormEvent, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

export default function LoginClient() {
  const router = useRouter();
  const params = useSearchParams();
  const [username, setUsername] = useState("reviewer");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    const res = await fetch("/api/login", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ password, username }),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      setError(data.error || "Invalid credentials");
      return;
    }
    router.push(params.get("next") || "/dashboard");
    router.refresh();
  }

  return (
    <section className="panel" style={{ maxWidth: 420 }}>
      <h1>Sign in</h1>
      <p>
        Internal research access only. Demo mode uses{" "}
        <code>AUTH_PASSWORD</code> (default <code>reglens-internal</code>).
        Postgres mode verifies <code>users.password_hash</code> (scrypt) and
        creates a DB session.
      </p>
      <form onSubmit={onSubmit}>
        <label>
          Username
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            style={{
              display: "block",
              width: "100%",
              margin: "0.4rem 0 1rem",
              padding: "0.5rem",
            }}
          />
        </label>
        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
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
