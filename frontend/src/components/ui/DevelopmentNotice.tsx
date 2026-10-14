import type { ReactNode } from 'react'

import { MILESTONES, type MilestoneKey } from '../../lib/milestones'

/** Makes the development status of an unfinished screen explicit to the user. */
export function DevelopmentNotice({
  milestone,
  children,
}: {
  milestone: MilestoneKey
  children: ReactNode
}) {
  const m = MILESTONES[milestone]
  return (
    <div
      role="note"
      className="rounded-xl border border-caution-200 bg-caution-50 px-4 py-3 text-sm text-caution-800"
    >
      <p className="font-semibold">
        In development · planned for {m.id}: {m.title}
      </p>
      <p className="mt-1 leading-relaxed">{children}</p>
    </div>
  )
}
