import Link from "next/link";
import { StatusNotice } from "@/components/StatusNotice";
import { loadRootManifest } from "@/lib/data";
import { instrumentCompletenessBadge, rootModeBadge } from "@/lib/mode";

export default function CollectionsPage() {
  const root = loadRootManifest();
  const mode = rootModeBadge(root);
  return (
    <>
      <h1 className="page-title">Collections</h1>
      <p className="meta">
        Dataset mode: <strong>{mode.label}</strong> — {mode.detail}
      </p>
      <StatusNotice variant="inline" />
      <div className="grid-2" style={{ marginTop: "1.25rem" }}>
        {root.instruments.map((inst) => {
          const badge = instrumentCompletenessBadge(inst);
          return (
            <article key={inst.slug} className="card">
              <div className="card-head">
                <h2 className="section-title" style={{ margin: 0 }}>
                  {inst.title}
                </h2>
                {badge ? (
                  <span className={`mode-badge tone-${badge.tone}`}>
                    {badge.label}
                  </span>
                ) : null}
              </div>
              <p className="meta">{badge?.detail}</p>
              {inst.available ? (
                <p className="meta">
                  {inst.version_count} snapshots · {inst.section_count} sections
                </p>
              ) : (
                <p className="meta">{inst.missing_reason}</p>
              )}
              <Link className="btn" href={`/instruments/${inst.slug}/`}>
                Open
              </Link>
            </article>
          );
        })}
      </div>
    </>
  );
}
