import { Link } from 'react-router'

import { Button } from '../components/ui/Button'
import { DevelopmentNotice } from '../components/ui/DevelopmentNotice'
import { TextField } from '../components/ui/FormField'
import { AuthCard } from '../features/auth/AuthCard'

export function RegisterPage() {
  return (
    <AuthCard
      title="Create your account"
      description="Register with a unique email address and a password."
      footer={
        <>
          Already registered?{' '}
          <Link to="/login" className="font-semibold text-brand-700 hover:underline">
            Log in
          </Link>
        </>
      }
    >
      <DevelopmentNotice milestone="auth">
        Registration is not available yet. Account creation (REQ-4.1.1) is implemented in the next
        milestone, so this form is disabled.
      </DevelopmentNotice>
      <form className="space-y-4" aria-label="Registration form" onSubmit={(e) => e.preventDefault()}>
        <fieldset disabled className="space-y-4">
          <TextField label="Full name" autoComplete="name" />
          <TextField label="Email" type="email" autoComplete="email" placeholder="you@example.com" />
          <TextField
            label="Password"
            type="password"
            autoComplete="new-password"
            hint="At least 8 characters."
          />
          <Button type="submit" className="w-full">
            Create account
          </Button>
        </fieldset>
      </form>
    </AuthCard>
  )
}
