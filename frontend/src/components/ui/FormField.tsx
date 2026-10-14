import {
  forwardRef,
  useId,
  type InputHTMLAttributes,
  type ReactNode,
  type SelectHTMLAttributes,
} from 'react'

import { cn } from '../../lib/cn'
import type { Option } from '../../lib/options'

const controlClasses =
  'mt-1.5 block w-full rounded-lg border bg-surface px-3 py-2 text-sm text-ink ' +
  'placeholder:text-ink-muted/70 disabled:cursor-not-allowed disabled:bg-surface-muted'

interface FieldProps {
  label: string
  hint?: ReactNode
  error?: string
}

function FieldShell({
  id,
  label,
  hint,
  error,
  children,
}: FieldProps & { id: string; children: ReactNode }) {
  return (
    <div>
      <label htmlFor={id} className="block text-sm font-medium text-ink">
        {label}
      </label>
      {children}
      {error ? (
        <p id={`${id}-error`} className="mt-1 text-xs font-medium text-danger-700">
          {error}
        </p>
      ) : (
        hint && (
          <p id={`${id}-hint`} className="mt-1 text-xs text-ink-muted">
            {hint}
          </p>
        )
      )}
    </div>
  )
}

export const TextField = forwardRef<HTMLInputElement, FieldProps & InputHTMLAttributes<HTMLInputElement>>(
  function TextField({ label, hint, error, className, ...props }, ref) {
    const id = useId()
    return (
      <FieldShell id={id} label={label} hint={hint} error={error}>
        <input
          ref={ref}
          id={id}
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? `${id}-error` : hint ? `${id}-hint` : undefined}
          className={cn(controlClasses, error ? 'border-danger-700' : 'border-line', className)}
          {...props}
        />
      </FieldShell>
    )
  },
)

export const SelectField = forwardRef<
  HTMLSelectElement,
  FieldProps & SelectHTMLAttributes<HTMLSelectElement> & { options: readonly Option[]; placeholder?: string }
>(function SelectField({ label, hint, error, options, placeholder, className, ...props }, ref) {
  const id = useId()
  return (
    <FieldShell id={id} label={label} hint={hint} error={error}>
      <select
        ref={ref}
        id={id}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? `${id}-error` : hint ? `${id}-hint` : undefined}
        className={cn(controlClasses, error ? 'border-danger-700' : 'border-line', className)}
        {...props}
      >
        {placeholder !== undefined && <option value="">{placeholder}</option>}
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </FieldShell>
  )
})

