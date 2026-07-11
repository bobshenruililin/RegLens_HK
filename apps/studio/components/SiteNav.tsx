"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import type { StudioRole } from "../lib/auth";

type Props = {
  role?: StudioRole | null;
  mode?: string;
};

export function SiteNav({ role, mode }: Props) {
  const router = useRouter();

  async function logout() {
    await fetch("/api/logout", { method: "POST" });
    router.push("/login");
    router.refresh();
  }

  return (
    <nav className="nav">
      <Link href="/dashboard">Dashboard</Link>
      <Link href="/jobs">Jobs</Link>
      <Link href="/review">Review</Link>
      <Link href="/releases">Releases</Link>
      <Link href="/audit">Audit</Link>
      <Link href="/search">Search</Link>
      <Link href="/documents">Documents</Link>
      <Link href="/decisions">Decisions</Link>
      <Link href="/research">Research</Link>
      <Link href="/pilot/core10">Pilot Core10</Link>
      <Link href="/issues">Issues</Link>
      <Link href="/sanctions">Sanctions</Link>
      <Link href="/authorities">Authorities</Link>
      <Link href="/research-pack">Research pack</Link>
      <Link href="/sync">Sync</Link>
      <Link href="/source-policies">Policies</Link>
      {role === "admin" && <Link href="/admin/users">Admin</Link>}
      {mode && (
        <span className="badge" title="REGLENS_MODE">
          {mode}
        </span>
      )}
      <button type="button" onClick={logout}>
        Sign out
      </button>
    </nav>
  );
}
