import ReviewClient from "@/components/ReviewClient";
import {
  loadRootManifest,
  loadTransition,
  loadTransitionsIndex,
} from "@/lib/data";

function pickReviewPairs(): Array<{
  id: string;
  instrument: string;
  from: string;
  to: string;
  section_id: string;
  relationship: string;
  heading?: string;
}> {
  type Pair = {
    id: string;
    instrument: string;
    from: string;
    to: string;
    section_id: string;
    relationship: string;
    heading?: string;
  };
  const root = loadRootManifest();
  const target = root.instruments.find((i) => i.slug === "cap-599g" && i.available)
    ? "cap-599g"
    : root.instruments.find((i) => i.available)?.slug;
  if (!target) return [];

  const transitions = loadTransitionsIndex(target).transitions as Array<{
    transition_id: string;
    from_version: string;
    to_version: string;
  }>;
  const buckets: Record<string, Pair[]> = {
    text_changed: [],
    status_changed: [],
    text_and_status_changed: [],
    added: [],
    removed: [],
  };
  const pairs: Pair[] = [];

  for (const t of transitions) {
    const data = loadTransition(target, t.transition_id) as {
      items: Array<{
        section_id: string;
        relationship: string;
        section_num_b?: string;
        section_num_a?: string;
      }>;
    };
    for (const item of data.items) {
      if (item.relationship === "unchanged") continue;
      const row: Pair = {
        id: `${t.transition_id}::${item.section_id}`,
        instrument: target,
        from: t.from_version,
        to: t.to_version,
        section_id: item.section_id,
        relationship: item.relationship,
        heading: item.section_num_b || item.section_num_a,
      };
      if (buckets[item.relationship]) buckets[item.relationship].push(row);
      pairs.push(row);
    }
  }

  const selected: Pair[] = [];
  const order = [
    "text_changed",
    "text_and_status_changed",
    "status_changed",
    "added",
    "removed",
  ];
  for (const key of order) {
    const bucket = buckets[key] || [];
    const step = Math.max(1, Math.floor(bucket.length / 8) || 1);
    for (let i = 0; i < bucket.length && selected.length < 30; i += step) {
      selected.push(bucket[i]);
    }
  }
  for (const p of pairs) {
    if (selected.length >= 30) break;
    if (!selected.find((s) => s.id === p.id)) selected.push(p);
  }
  return selected.slice(0, 30);
}

/** Copied into app/review only when LAWTRACE_LOCAL_REVIEW=1. */
export default function ReviewPage() {
  const pairs = pickReviewPairs();
  return (
    <>
      <p className="meta">
        This local review workspace is available only in explicit local-review
        builds. It is not linked from ordinary navigation — open{" "}
        <code>/review/</code> directly.
      </p>
      <ReviewClient pairs={pairs} />
    </>
  );
}
