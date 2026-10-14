import { ApiStatusIndicator } from '../../features/health/ApiStatusIndicator'

export function SiteFooter() {
  return (
    <footer className="border-t border-line bg-surface-muted/60 print:hidden">
      <div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-6 text-sm text-ink-muted sm:px-6 md:flex-row md:items-center md:justify-between">
        <ApiStatusIndicator />
        <p className="max-w-xl md:text-right">
          Nutrition values in NutriPlan are estimates, not medical advice. If you have a medical
          dietary restriction, consult a qualified professional.
        </p>
      </div>
    </footer>
  )
}
