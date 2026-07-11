import Link from "next/link";
import { SyntheticBanner } from "@/components/SyntheticBanner";
import { exploreHref, loadRelease } from "@/lib/release";

export const metadata = {
  title: "Research questions",
};

const QUESTIONS = [
  {
    question: "Which synthetic decisions involve recordkeeping issues?",
    href: exploreHref({ issue: "recordkeeping" }),
    note: "Starts with the issue taxonomy, then reviewers can inspect evidence-backed propositions.",
  },
  {
    question: "How do warning outcomes appear in the demo corpus?",
    href: exploreHref({ sanction: "warning" }),
    note: "Filters by sanction category; counts describe only the current synthetic release.",
  },
  {
    question: "Which MCHK demo records mention admissions?",
    href: exploreHref({ q: "admission", regulator: "MCHK" }),
    note: "Keyword matching is limited to catalog fields, not full-text or semantic search.",
  },
  {
    question: "Where do premises or equipment issues appear?",
    href: exploreHref({ issue: "premises_equipment" }),
    note: "A synthetic DCHK example demonstrates issue-to-sanction navigation.",
  },
  {
    question: "Which demo records include costs as a sanction category?",
    href: exploreHref({ sanction: "costs" }),
    note: "Use decision pages to inspect exact synthetic proposition wording.",
  },
] as const;

export default function QuestionsPage() {
  const release = loadRelease();

  return (
    <>
      <SyntheticBanner kind={release.kind} version={release.version} />

      <header className="page-hero">
        <h1>Research questions</h1>
        <p className="lede">
          Starter prompts for exploring the synthetic demo corpus. These links
          open structured filters in Explore and should not be read as findings
          about real-world disciplinary prevalence.
        </p>
      </header>

      <section className="section" aria-labelledby="questions-heading">
        <h2 id="questions-heading">Try a question</h2>
        <ul className="decision-list">
          {QUESTIONS.map((item) => (
            <li className="decision-card" key={item.question}>
              <h3>
                <Link href={item.href}>{item.question}</Link>
              </h3>
              <p>{item.note}</p>
            </li>
          ))}
        </ul>
      </section>

      <section className="section" aria-labelledby="limits-heading">
        <h2 id="limits-heading">Interpretation limits</h2>
        <p>
          Observatory filters are public, static, and descriptive. Core10 real
          research questions belong in Studio/private review until source policy,
          legal approval, and release scans permit a public real release.
        </p>
        <div className="link-row">
          <Link className="btn" href="/tour/">
            Take the guided tour
          </Link>
          <Link className="btn btn--ghost" href="/methodology/">
            Read methodology
          </Link>
        </div>
      </section>
    </>
  );
}
