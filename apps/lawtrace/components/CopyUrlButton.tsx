"use client";

import { useState } from "react";

/** Copy the current page URL — for stable deep links. */
export function CopyUrlButton() {
  const [status, setStatus] = useState<"idle" | "copied" | "failed">("idle");

  async function onCopy() {
    try {
      const url = window.location.href;
      await navigator.clipboard.writeText(url);
      setStatus("copied");
      window.setTimeout(() => setStatus("idle"), 2000);
    } catch {
      setStatus("failed");
      window.setTimeout(() => setStatus("idle"), 2500);
    }
  }

  return (
    <span className="copy-url">
      <button type="button" className="btn secondary" onClick={onCopy}>
        Copy page URL
      </button>
      <span className="meta" aria-live="polite">
        {status === "copied"
          ? " Copied."
          : status === "failed"
            ? " Copy failed — use the address bar."
            : ""}
      </span>
    </span>
  );
}
