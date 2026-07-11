import Link from "next/link";
import type { CatalogDecision } from "@/lib/release";

type DecisionCardProps = {
  decision: CatalogDecision;
  selectable?: boolean;
  selected?: boolean;
  onToggleSelect?: (slug: string) => void;
};

export function DecisionCard({
  decision,
  selectable = false,
  selected = false,
  onToggleSelect,
}: DecisionCardProps) {
  return (
    <article className="decision-card">
      <h3>
        <Link href={`/decisions/${decision.slug}/`}>{decision.title}</Link>
      </h3>
      <div className="meta-row">
        <span>{decision.regulator_code}</span>
        {decision.profession ? <span>{decision.profession}</span> : null}
        {decision.decision_date ? <span>{decision.decision_date}</span> : null}
        {decision.case_ref ? <span>{decision.case_ref}</span> : null}
      </div>
      {decision.summary ? <p>{decision.summary}</p> : null}
      {(decision.issues || []).length > 0 || (decision.sanctions || []).length > 0 ? (
        <ul className="tag-list" aria-label="Issues and sanctions">
          {(decision.issues || []).map((i) => (
            <li key={`i-${i}`}>Issue: {i}</li>
          ))}
          {(decision.sanctions || []).map((s) => (
            <li key={`s-${s}`}>Sanction: {s}</li>
          ))}
        </ul>
      ) : null}
      {selectable && onToggleSelect ? (
        <p style={{ marginTop: "0.75rem" }}>
          <label>
            <input
              type="checkbox"
              checked={selected}
              onChange={() => onToggleSelect(decision.slug)}
            />{" "}
            Compare
          </label>
        </p>
      ) : null}
    </article>
  );
}
