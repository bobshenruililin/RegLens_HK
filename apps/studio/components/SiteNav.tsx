"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

export function SiteNav() {
  const router = useRouter();

  async function logout() {
    await fetch("/api/logout", { method: "POST" });
    router.push("/login");
    router.refresh();
  }

  return (
    <nav className="nav">
      <Link href="/">Home</Link>
      <Link href="/search">Search</Link>
      <Link href="/review">Review</Link>
      <button type="button" onClick={logout}>
        Sign out
      </button>
    </nav>
  );
}
