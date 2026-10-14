import { useId, type InputHTMLAttributes, type ReactNode, type SelectHTMLAttributes } from 'react'

const controlClasses =
  'mt-1.5 block w-full rounded-lg border border-line bg-surface px-3 py-2 text-sm text-ink ' +
  'placeholder:text-ink-muted/70 disabled:cursor-not-allowed disabled:bg-surface-muted'

interface FieldProps {
  label: string
  hint?: ReactNode
}

export function TextField({ label, hint, ...props }: FieldProps & InputHTMLAttributes<HTMLInputElement>) {
  const id = useId()
  return (
    <div>
      <label htmlFor={id} className="block text-sm font-medium text-ink">
        {label}
      </label>
      <input id={id} className={controlClasses} {...props} />
      {hint && <p className="mt-1 text-xs text-ink-muted">{hint}</p>}
    </div>
  )
}

export function SelectField({
  label,
  hint,
  options,
  ...props
}: FieldProps & SelectHTMLAttributes<HTMLSelectElement> & { options: readonly string[] }) {
  const id = useId()
  return (
    <div>
      <label htmlFor={id} className="block text-sm font-medium text-ink">
        {label}
      </label>
      <select id={id} className={controlClasses} {...props}>
        {options.map((option) => (
          <option key={option}>{option}</option>
        ))}
      </select>
      {hint && <p className="mt-1 text-xs text-ink-muted">{hint}</p>}
    </div>
  )
}
