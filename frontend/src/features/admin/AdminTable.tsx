import { useId, type ReactNode } from 'react'

export function AdminTable({
  caption,
  headers,
  rows,
  rowKeys,
}: {
  caption: string
  headers: string[]
  rows: ReactNode[][]
  rowKeys: (string | number)[]
}) {
  if (!rows.length) {
    return <p className="rounded-xl border border-dashed border-line px-4 py-8 text-center text-sm text-ink-muted">No records found.</p>
  }
  return (
    <div className="overflow-x-auto rounded-2xl border border-line bg-surface">
      <table className="w-full min-w-[640px] text-left text-sm">
        <caption className="sr-only">{caption}</caption>
        <thead>
          <tr className="border-b border-line bg-surface-muted/70">
            {headers.map((h, i) => (
              <th key={i} scope="col" className="px-3 py-2.5 font-semibold text-ink">
                {h || <span className="sr-only">Actions</span>}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((cells, r) => (
            <tr key={rowKeys[r]} className="border-b border-line align-top last:border-0">
              {cells.map((cell, c) => (
                <td key={c} className="px-3 py-2.5 text-ink-muted">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function SearchBox({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  const id = useId()
  return (
    <div className="w-full max-w-xs">
      <label htmlFor={id} className="block text-sm font-medium text-ink">
        {label}
      </label>
      <input
        id={id}
        type="search"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="mt-1.5 block w-full rounded-lg border border-line bg-surface px-3 py-2 text-sm"
      />
    </div>
  )
}
