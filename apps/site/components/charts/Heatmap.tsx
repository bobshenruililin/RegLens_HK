import Link from "next/link";
import type { IssueSanctionCount } from "@/lib/release";
import { exploreHref } from "@/lib/release";

type HeatmapProps = {
  title: string;
  cells: IssueSanctionCount[];
  emptyMessage?: string;
};

function intensity(count: number, max: number): string {
  if (max <= 0 || count <= 0) return "transparent";
  const t = Math.min(1, count / max);
  const alpha = 0.12 + t * 0.72;
  return `rgba(13, 110, 110, ${alpha.toFixed(3)})`;
}

export function Heatmap({
  title,
  cells,
  emptyMessage = "No issue × sanction pairs in this release.",
}: HeatmapProps) {
  if (cells.length === 0) {
    return (
      <div className="chart-block">
        <h3>{title}</h3>
        <p className="empty-state">{emptyMessage}</p>
      </div>
    );
  }

  const issues = Array.from(new Set(cells.map((c) => c.issue))).sort();
  const sanctions = Array.from(new Set(cells.map((c) => c.sanction))).sort();
  const lookup = new Map(
    cells.map((c) => [`${c.issue}||${c.sanction}`, c.count]),
  );
  const max = Math.max(...cells.map((c) => c.count), 1);

  return (
    <div className="chart-block">
      <h3>{title}</h3>
      <div className="heatmap" role="group" aria-label={title}>
        <table>
          <caption className="sr-only">{title}</caption>
          <thead>
            <tr>
              <th scope="col">Issue \\ Sanction</th>
              {sanctions.map((s) => (
                <th key={s} scope="col">
                  {s}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {issues.map((issue) => (
              <tr key={issue}>
                <th scope="row">{issue}</th>
                {sanctions.map((sanction) => {
                  const count = lookup.get(`${issue}||${sanction}`) || 0;
                  const href = exploreHref({ issue, sanction });
                  return (
                    <td
                      key={sanction}
                      style={{ background: intensity(count, max) }}
                    >
                      {count > 0 ? (
                        <Link
                          href={href}
                          aria-label={`${issue} × ${sanction}: ${count}`}
                        >
                          {count}
                        </Link>
                      ) : (
                        <span aria-hidden="true">·</span>
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
