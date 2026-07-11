import Link from "next/link";
import { SyntheticBanner } from "@/components/SyntheticBanner";
import { loadRelease } from "@/lib/release";

export const metadata = {
  title: "Roadmap",
};

const ROADMAP = [
  {
    phase: "Synthetic demo",
    status: "Current public Pages posture",
    description:
      "Use synthetic fixtures to demonstrate extraction, review, release scans, and static Observatory UX.",
  },
  {
    phase: "Core10",
    status: "Internal readiness loop",
    description:
      "Run metadata sync, acquisition, extraction, review, and internal research on a small real-corpus set in Studio/private storage.",
  },
  {
    phase: "Core50",
    status: "Internal scale pilot",
    description:
      "Expand the reviewed real-corpus pilot to the Core50 plan while preserving source-policy and privacy gates.",
  },
  {
    phase: "Legal approval",
    status: "Required before public real release",
    description:
      "Confirm source permissions, privacy posture, publication policy, and release copy before any real data leaves Studio.",
  },
  {
    phase: "Public real release",
    status: "Future only",
    description:
      "If approved, publish a checked release with reviewed propositions, caveats, and scans. Until then, Pages remains synthetic/demo.",
  },
] as const;

export default function RoadmapPage() {
  const release = loadRelease();

  return (
    <>
      <SyntheticBanner kind={release.kind} version={release.version} />

      <header className="page-hero">
        <h1>Roadmap</h1>
        <p className="lede">
          RegLens moves from synthetic public demonstration to internal Core10,
          then Core50, then legal approval before any public real-corpus release.
          GitHub Pages is public.
        </p>
      </header>

      <section className="section" aria-labelledby="roadmap-heading">
        <h2 id="roadmap-heading">Release path</h2>
        <div className="timeline" role="list">
          {ROADMAP.map((item, index) => (
            <article className="timeline__row" role="listitem" key={item.phase}>
              <div className="timeline__year">Step {index + 1}</div>
              <div className="compare-col">
                <h3>{item.phase}</h3>
                <p className="meta-row">{item.status}</p>
                <p>{item.description}</p>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="section" aria-labelledby="boundary-heading">
        <h2 id="boundary-heading">Boundary that does not move automatically</h2>
        <p>
          Public availability of regulator material, robots.txt, or
          student-research letters do not by themselves authorize Pages
          publication. Real corpus material stays in Studio/private storage
          until approval and source policy change.
        </p>
        <div className="link-row">
          <Link className="btn" href="/questions/">
            Browse research questions
          </Link>
          <Link className="btn btn--ghost" href="/data/">
            View current demo release data
          </Link>
        </div>
      </section>
    </>
  );
}
