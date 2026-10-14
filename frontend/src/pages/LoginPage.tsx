import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link, useNavigate, useSearchParams } from 'react-router'

import { Alert } from '../components/ui/Alert'
import { Button } from '../components/ui/Button'
import { TextField } from '../components/ui/FormField'
import { AuthCard } from '../features/auth/AuthCard'
import { loginSchema, type LoginValues } from '../features/auth/schemas'
import { useAuth } from '../hooks/useAuth'
import { errorMessage } from '../lib/apiClient'
import { safeNext } from '../lib/safeNext'


export function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const [serverError, setServerError] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginValues>({ resolver: zodResolver(loginSchema) })

  async function onSubmit(values: LoginValues) {
    setServerError(null)
    try {
      const session = await login(values.email, values.password)
      const next = safeNext(params.get('next'))
      navigate(next ?? (session.has_profile ? '/dashboard' : '/profile'), { replace: true })
    } catch (error) {
      setServerError(errorMessage(error))
    }
  }

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
      {serverError && <Alert tone="error">{serverError}</Alert>}
      <form className="space-y-4" aria-label="Login form" noValidate onSubmit={handleSubmit(onSubmit)}>
        <TextField
          label="Email"
          type="email"
          autoComplete="email"
          placeholder="you@example.com"
          error={errors.email?.message}
          {...register('email')}
        />
        <TextField
          label="Password"
          type="password"
          autoComplete="current-password"
          error={errors.password?.message}
          {...register('password')}
        />
        <Button type="submit" className="w-full" disabled={isSubmitting}>
          {isSubmitting ? 'Logging in…' : 'Log in'}
        </Button>
      </form>
    </AuthCard>
  )
}
