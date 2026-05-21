"use client";

interface Column<T> {
  key: string;
  header: string;
  render?: (row: T) => React.ReactNode;
  className?: string;
}

interface Props<T> {
  columns: Column<T>[];
  data: T[];
  keyFn: (row: T) => string | number;
  onRowClick?: (row: T) => void;
}

export function DataTable<T>({ columns, data, keyFn, onRowClick }: Props<T>) {
  return (
    <div className="overflow-x-auto rounded-xl border border-[#334155]">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-[#1e293b] border-b border-[#334155]">
            {columns.map((col) => (
              <th
                key={col.key}
                className={`px-4 py-3 text-left text-slate-400 font-medium text-xs uppercase tracking-wide ${col.className ?? ""}`}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row) => (
            <tr
              key={keyFn(row)}
              onClick={() => onRowClick?.(row)}
              className={`border-b border-[#334155] last:border-0 bg-[#1e293b] hover:bg-[#273549] transition-colors ${
                onRowClick ? "cursor-pointer" : ""
              }`}
            >
              {columns.map((col) => (
                <td key={col.key} className={`px-4 py-3 text-slate-300 ${col.className ?? ""}`}>
                  {col.render
                    ? col.render(row)
                    : String((row as Record<string, unknown>)[col.key] ?? "—")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
