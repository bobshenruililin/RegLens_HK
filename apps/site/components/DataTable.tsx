import Link from "next/link";

export type DataTableColumn<T> = {
  key: string;
  header: string;
  render: (row: T) => React.ReactNode;
};

type DataTableProps<T> = {
  caption: string;
  columns: DataTableColumn<T>[];
  rows: T[];
  emptyMessage?: string;
};

export function DataTable<T>({
  caption,
  columns,
  rows,
  emptyMessage = "No rows in this release.",
}: DataTableProps<T>) {
  if (rows.length === 0) {
    return (
      <div className="data-table-wrap">
        <p className="empty-state">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="data-table-wrap">
      <table className="data-table">
        <caption>{caption}</caption>
        <thead>
          <tr>
            {columns.map((col) => (
              <th key={col.key} scope="col">
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, idx) => (
            <tr key={idx}>
              {columns.map((col) => (
                <td key={col.key}>{col.render(row)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

type LinkedCountRow = {
  label: string;
  count: number;
  href: string;
};

export function LinkedCountTable({
  caption,
  rows,
}: {
  caption: string;
  rows: LinkedCountRow[];
}) {
  return (
    <DataTable
      caption={caption}
      rows={rows}
      columns={[
        {
          key: "label",
          header: "Category",
          render: (r) => <Link href={r.href}>{r.label}</Link>,
        },
        {
          key: "count",
          header: "Count",
          render: (r) => r.count,
        },
      ]}
    />
  );
}
