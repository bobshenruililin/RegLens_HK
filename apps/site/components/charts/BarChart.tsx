import { withBasePath } from "@/lib/release";

export type BarItem = {
  label: string;
  count: number;
  href?: string;
};

type BarChartProps = {
  title: string;
  items: BarItem[];
  emptyMessage?: string;
};

export function BarChart({
  title,
  items,
  emptyMessage = "No data in this release.",
}: BarChartProps) {
  if (items.length === 0) {
    return (
      <div className="chart-block">
        <h3>{title}</h3>
        <p className="empty-state">{emptyMessage}</p>
      </div>
    );
  }

  const max = Math.max(...items.map((i) => i.count), 1);
  const barWidth = 36;
  const gap = 16;
  const chartH = 160;
  const padTop = 16;
  const padBottom = 36;
  const padLeft = 8;
  const width = padLeft + items.length * (barWidth + gap);
  const height = chartH + padTop + padBottom;

  return (
    <div className="chart-block">
      <h3>{title}</h3>
      <div className="bar-chart" role="img" aria-label={`${title} bar chart`}>
        <svg
          viewBox={`0 0 ${width} ${height}`}
          width={width}
          height={height}
          aria-hidden="true"
        >
          {items.map((item, idx) => {
            const h = (item.count / max) * chartH;
            const x = padLeft + idx * (barWidth + gap);
            const y = padTop + chartH - h;
            const content = (
              <>
                <rect
                  className="bar"
                  x={x}
                  y={y}
                  width={barWidth}
                  height={Math.max(h, 1)}
                  rx={1}
                />
                <text
                  className="axis-label"
                  x={x + barWidth / 2}
                  y={padTop + chartH + 16}
                  textAnchor="middle"
                >
                  {item.label}
                </text>
                <text
                  className="axis-label"
                  x={x + barWidth / 2}
                  y={y - 4}
                  textAnchor="middle"
                >
                  {item.count}
                </text>
              </>
            );
            return item.href ? (
              <a key={item.label} href={withBasePath(item.href)}>
                {content}
              </a>
            ) : (
              <g key={item.label}>{content}</g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}
