import { useId, useMemo, useState } from 'react'

import type { NamedRef } from '../../types/api'

/** Pick specific foods to avoid (e.g. mushrooms) in addition to allergen categories. */
export function FoodExclusionPicker({
  foods,
  selected,
  onChange,
}: {
  foods: NamedRef[]
  selected: number[]
  onChange: (ids: number[]) => void
}) {
  const [query, setQuery] = useState('')
  const id = useId()
  const byId = useMemo(() => new Map(foods.map((f) => [f.id, f])), [foods])
  const matches = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return []
    return foods.filter((f) => f.name.toLowerCase().includes(q) && !selected.includes(f.id)).slice(0, 8)
  }, [foods, query, selected])

  return (
    <div>
      <label htmlFor={id} className="block text-sm font-medium text-ink">
        Other foods you can’t eat
      </label>
      <input
        id={id}
        type="search"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder={foods.length ? 'Search foods, e.g. mushroom' : 'No foods in the catalogue yet'}
        disabled={!foods.length}
        className="mt-1.5 block w-full rounded-lg border border-line bg-surface px-3 py-2 text-sm"
      />
      {matches.length > 0 && (
        <ul className="mt-1 max-h-48 overflow-y-auto rounded-lg border border-line bg-surface" aria-label="Matching foods">
          {matches.map((f) => (
            <li key={f.id}>
              <button
                type="button"
                className="w-full px-3 py-2 text-left text-sm hover:bg-brand-50"
                onClick={() => {
                  onChange([...selected, f.id])
                  setQuery('')
                }}
              >
                Exclude {f.name}
              </button>
            </li>
          ))}
        </ul>
      )}
      {selected.length > 0 && (
        <ul className="mt-2 flex flex-wrap gap-2" aria-label="Excluded foods">
          {selected.map((fid) => (
            <li key={fid}>
              <button
                type="button"
                onClick={() => onChange(selected.filter((x) => x !== fid))}
                className="inline-flex items-center gap-1.5 rounded-full bg-danger-50 px-3 py-1 text-sm text-danger-700 ring-1 ring-danger-200"
                aria-label={`Remove ${byId.get(fid)?.name ?? 'food'}`}
              >
                {byId.get(fid)?.name ?? `Food #${fid}`} <span aria-hidden="true">✕</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
