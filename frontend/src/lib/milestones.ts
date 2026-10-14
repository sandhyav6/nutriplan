/** Development milestones (docs/development-roadmap.md) referenced by in-app status notices. */
export const MILESTONES = {
  foundation: { id: 'M0', title: 'Project foundation' },
  auth: { id: 'M1', title: 'Authentication & user profiles' },
  catalogue: { id: 'M2', title: 'Food catalogue & admin panel' },
  planner: { id: 'M3', title: 'Rule engine & weekly meal plans' },
  grocery: { id: 'M4', title: 'Grocery list generator' },
  feedback: { id: 'M5', title: 'Feedback & meal replacement' },
  dashboard: { id: 'M6', title: 'Dashboard, hardening & release' },
} as const

export type MilestoneKey = keyof typeof MILESTONES
