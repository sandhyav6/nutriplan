import {
  Bar,
  BarChart,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { DAYS, formatKcal } from '../../lib/format'
import type { DayTotals } from '../../types/api'

// Validated against the light surface with the dataviz palette checker (lightness, chroma, ≥3:1).
const BAR = '#25935f'
const INK_MUTED = '#56615a'
const GRID = '#e3dccf'

interface Datum {
  day: string
  calories: number
  protein: number
}

function ChartTooltip({ active, payload }: { active?: boolean; payload?: { payload: Datum }[] }) {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div className="rounded-lg border border-line bg-surface px-3 py-2 text-xs shadow-md">
      <p className="font-semibold text-ink">{d.day}</p>
      <p className="text-ink">{formatKcal(d.calories)}</p>
      <p className="text-ink-muted">{Math.round(d.protein)} g protein</p>
    </div>
  )
}

/** Single-series bar chart: planned calories per day against the daily target. */
export function DailyCaloriesChart({ days, target }: { days: DayTotals[]; target: number }) {
  const data: Datum[] = days.map((d) => ({
    day: DAYS[d.day_of_week],
    calories: Number(d.calories_kcal),
    protein: Number(d.protein_g),
  }))
  return (
    <figure>
      <div className="h-64 w-full" aria-hidden="true">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 16, right: 8, bottom: 0, left: -8 }} barCategoryGap="30%">
            <CartesianGrid vertical={false} stroke={GRID} strokeDasharray="0" />
            <XAxis
              dataKey="day"
              tickFormatter={(v: string) => v.slice(0, 3)}
              tick={{ fill: INK_MUTED, fontSize: 12 }}
              axisLine={{ stroke: GRID }}
              tickLine={false}
            />
            <YAxis tick={{ fill: INK_MUTED, fontSize: 12 }} axisLine={false} tickLine={false} width={48} />
            <Tooltip content={<ChartTooltip />} cursor={{ fill: 'rgba(37,147,95,0.08)' }} />
            <ReferenceLine
              y={target}
              stroke={INK_MUTED}
              strokeDasharray="4 4"
              label={{ value: `Target ${target}`, position: 'insideTopRight', fill: INK_MUTED, fontSize: 11 }}
            />
            <Bar dataKey="calories" fill={BAR} radius={[4, 4, 0, 0]} maxBarSize={40} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      {/* Accessible table view of the same data */}
      <figcaption className="sr-only">Planned calories per day compared with a target of {target} kcal.</figcaption>
      <table className="sr-only">
        <thead>
          <tr>
            <th scope="col">Day</th>
            <th scope="col">Calories</th>
            <th scope="col">Protein (g)</th>
          </tr>
        </thead>
        <tbody>
          {data.map((d) => (
            <tr key={d.day}>
              <td>{d.day}</td>
              <td>{Math.round(d.calories)}</td>
              <td>{Math.round(d.protein)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </figure>
  )
}
