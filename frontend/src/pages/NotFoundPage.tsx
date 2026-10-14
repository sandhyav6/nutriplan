import { ButtonLink } from '../components/ui/Button'
import { EmptyState } from '../components/ui/StateViews'

export function NotFoundPage() {
  return (
    <div className="py-10">
      <h1 className="sr-only">Page not found</h1>
      <EmptyState
        title="404 – page not found"
        action={<ButtonLink to="/">Back to home</ButtonLink>}
      >
        The page you are looking for does not exist or has moved.
      </EmptyState>
    </div>
  )
}
