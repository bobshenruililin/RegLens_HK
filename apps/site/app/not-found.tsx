import Link from "next/link";

export default function NotFound() {
  return (
    <header className="page-hero">
      <h1>Page not found</h1>
      <p className="lede">
        That route is not part of this static export. The Observatory has no
        server-side router beyond pre-rendered pages.
      </p>
      <div className="link-row">
        <Link className="btn" href="/">
          Home
        </Link>
        <Link className="btn btn--ghost" href="/explore/">
          Explore
        </Link>
      </div>
    </header>
  );
}
