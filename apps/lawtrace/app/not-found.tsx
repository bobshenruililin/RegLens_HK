import Link from "next/link";

export default function NotFound() {
  return (
    <>
      <h1 className="page-title">Not found</h1>
      <p className="muted">That LawTrace route is unavailable in this data mode.</p>
      <p>
        <Link href="/">Return home</Link>
      </p>
    </>
  );
}
