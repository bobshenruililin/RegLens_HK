"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

export function ReleaseApproveButton({
  publicationReleaseId,
  expectedVersion,
  disabled,
}: {
  publicationReleaseId: string;
  expectedVersion: number;
  disabled?: boolean;
}) {
  const router = useRouter();
  const [csrf, setCsrf] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    fetch("/api/csrf")
      .then((r) => r.json())
      .then((d) => setCsrf(d.csrf || null))
      .catch(() => undefined);
  }, []);

  async function approve() {
    setBusy(true);
    setMessage(null);
    const res = await fetch("/api/pg/releases", {
      method: "POST",
      headers: {
        "content-type": "application/json",
        ...(csrf ? { "x-csrf-token": csrf } : {}),
      },
      body: JSON.stringify({
        publication_release_id: publicationReleaseId,
        expected_version: expectedVersion,
        csrf,
      }),
    });
    const data = await res.json();
    setBusy(false);
    if (!res.ok) {
      const detail = data.errors?.length
        ? data.errors.join("; ")
        : data.error || "Approve failed";
      setMessage(detail);
      return;
    }
    setMessage(`Approved → ${data.status} (v${data.version})`);
    router.refresh();
  }

  return (
    <div style={{ marginTop: "1rem" }}>
      <button type="button" onClick={approve} disabled={disabled || busy}>
        {busy ? "Validating…" : "Validate & approve"}
      </button>
      {message && <p className="warning">{message}</p>}
    </div>
  );
}
