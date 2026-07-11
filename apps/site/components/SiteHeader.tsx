"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { href: "/explore/", label: "Explore" },
  { href: "/compare/", label: "Compare" },
  { href: "/analytics/", label: "Analytics" },
  { href: "/methodology/", label: "Methodology" },
  { href: "/data/", label: "Data" },
] as const;

function isCurrent(pathname: string, href: string): boolean {
  if (href === "/") return pathname === "/" || pathname === "";
  return pathname === href || pathname.startsWith(href);
}

export function SiteHeader() {
  const pathname = usePathname() || "/";

  return (
    <header className="site-header">
      <div className="site-header__inner">
        <Link className="site-brand" href="/">
          RegLens Observatory
        </Link>
        <nav aria-label="Primary">
          <ul className="site-nav">
            {NAV.map((item) => (
              <li key={item.href}>
                <Link
                  href={item.href}
                  aria-current={isCurrent(pathname, item.href) ? "page" : undefined}
                >
                  {item.label}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
      </div>
    </header>
  );
}
