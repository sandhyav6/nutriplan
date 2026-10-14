import { Link } from 'react-router'

import { Button } from '../components/ui/Button'
import { DevelopmentNotice } from '../components/ui/DevelopmentNotice'
import { TextField } from '../components/ui/FormField'
import { AuthCard } from '../features/auth/AuthCard'

export function LoginPage() {
  return (
    <AuthCard
      title="Log in"
      description="Access your meal plans, grocery lists and dashboard."
      footer={
        <>
          New to NutriPlan?{' '}
          <Link to="/register" className="font-semibold text-brand-700 hover:underline">
            Create an account
          </Link>
        </>
      }
    >
      <DevelopmentNotice milestone="auth">
        Login is not available yet. Secure authentication with hashed passwords is implemented in
        the next milestone, so this form is disabled.
      </DevelopmentNotice>
      <form className="space-y-4" aria-label="Login form" onSubmit={(e) => e.preventDefault()}>
        <fieldset disabled className="space-y-4">
          <TextField label="Email" type="email" autoComplete="email" placeholder="you@example.com" />
          <TextField label="Password" type="password" autoComplete="current-password" />
          <Button type="submit" className="w-full">
            Log in
          </Button>
        </fieldset>
      </form>
    </AuthCard>
  )
}
