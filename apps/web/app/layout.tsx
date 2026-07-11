import type { Metadata } from "next";
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
        </header>
        <main>{children}</main>
        <footer className="site-footer">
          Internal research use only. Primary sources remain authoritative.
        </footer>
      </body>
    </html>
  );
}
