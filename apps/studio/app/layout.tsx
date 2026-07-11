import type { Metadata } from "next";
import { SiteNav } from "../components/SiteNav";
import { getCurrentUser } from "../lib/auth-server";
import { getMode } from "../lib/mode";
import "./globals.css";

export const metadata: Metadata = {
  title: "RegLens Studio",
  description:
    "Internal evidence-linked Hong Kong regulatory disciplinary review (Studio).",
};

export const dynamic = "force-dynamic";

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  let role = null;
  try {
    const user = await getCurrentUser();
    role = user?.role ?? null;
  } catch {
    role = null;
  }
  const mode = getMode();

  return (
    <html lang="en">
      <body>
        <header className="site-header">
          <div className="brand">RegLens Studio</div>
          <p className="tagline">
            Internal operator surface — not legal advice · not Observatory
          </p>
          <SiteNav role={role} mode={mode} />
        </header>
        <main>{children}</main>
        <footer className="site-footer">
          Internal / non-commercial research use only. Primary sources remain
          authoritative. No public republication of real judgments.
        </footer>
      </body>
    </html>
  );
}
