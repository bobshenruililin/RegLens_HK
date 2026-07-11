import type { Metadata } from "next";
import { SiteNav } from "../components/SiteNav";
import "./globals.css";

export const metadata: Metadata = {
  title: "RegLens HK",
  description:
    "Evidence-linked Hong Kong regulatory disciplinary decisions (internal research tool).",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <header className="site-header">
          <div className="brand">RegLens HK</div>
          <p className="tagline">
            Evidence-linked disciplinary data — not legal advice
          </p>
          <SiteNav />
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
