export interface Option {
  value: string
  label: string
}

/** Turns a label map into select options. */
export function toOptions<K extends string>(labels: Record<K, string>): Option[] {
  return (Object.keys(labels) as K[]).map((value) => ({ value, label: labels[value] }))
}
