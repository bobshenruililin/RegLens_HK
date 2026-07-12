import type { Metadata } from "next";
import { IBM_Plex_Sans, Source_Serif_4 } from "next/font/google";
import { SiteFooter, SiteHeader } from "@/components/Chrome";
import { loadRootManifest } from "@/lib/data";
import { rootModeBadge } from "@/lib/mode";
import "./globals.css";

const serif = Source_Serif_4({
  subsets: ["latin"],
  variable: "--font-source-serif",
  display: "swap",
});

const sans = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-ibm-plex",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "LawTrace HK",
    template: "%s · LawTrace HK",
  },
  description:
    "Compare two official open-data versions of a Hong Kong legislative section and inspect what changed.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const root = loadRootManifest();
  const mode = rootModeBadge(root);
  return (
    <html lang="en" className={`${serif.variable} ${sans.variable}`}>
      <body
        style={
          {
            ["--font-display" as string]: "var(--font-source-serif), Georgia, serif",
            ["--font-body" as string]: "var(--font-ibm-plex), Helvetica, sans-serif",
          } as React.CSSProperties
        }
      >
        <a className="skip-link" href="#main">
          Skip to content
        </a>
        <div className="shell">
          {/* Local review workspace is never linked from ordinary navigation. */}
          <SiteHeader mode={mode} review={false} />
          <main id="main" className="main">
            {children}
          </main>
          <SiteFooter />
        </div>
      </body>
    </html>
  );
}
