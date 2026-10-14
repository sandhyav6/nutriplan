import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link, useNavigate } from 'react-router'

import { Alert } from '../components/ui/Alert'
import { Button } from '../components/ui/Button'
import { TextField } from '../components/ui/FormField'
import { AuthCard } from '../features/auth/AuthCard'
import { registerSchema, type RegisterValues } from '../features/auth/schemas'
import { useAuth } from '../hooks/useAuth'
import { ApiError, errorMessage, fieldErrors } from '../lib/apiClient'

export function RegisterPage() {
  const { register: registerAccount } = useAuth()
  const navigate = useNavigate()
  const [serverError, setServerError] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<RegisterValues>({ resolver: zodResolver(registerSchema) })

  async function onSubmit(values: RegisterValues) {
    setServerError(null)
    try {
      await registerAccount(values.fullName, values.email, values.password)
      navigate('/profile', { replace: true }) // UC-01 step 5 – continue to profile setup
    } catch (error) {
      if (error instanceof ApiError && error.status === 409) {
        setError('email', { message: error.message })
        return
      }
      const fields = fieldErrors(error)
      if (fields.email) setError('email', { message: fields.email })
      if (fields.password) setError('password', { message: fields.password })
      if (fields.full_name) setError('fullName', { message: fields.full_name })
      if (!Object.keys(fields).length) setServerError(errorMessage(error))
    }
  }

  return (
    <AuthCard
      title="Create your account"
      description="Register with your email address to start planning meals."
      footer={
        <>
          Already registered?{' '}
          <Link to="/login" className="font-semibold text-brand-700 hover:underline">
            Log in
          </Link>
        </>
      }
    >
      {serverError && <Alert tone="error">{serverError}</Alert>}
      <form className="space-y-4" aria-label="Registration form" noValidate onSubmit={handleSubmit(onSubmit)}>
        <TextField label="Full name" autoComplete="name" error={errors.fullName?.message} {...register('fullName')} />
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
          autoComplete="new-password"
          hint="At least 8 characters, with a letter and a number."
          error={errors.password?.message}
          {...register('password')}
        />
        <TextField
          label="Confirm password"
          type="password"
          autoComplete="new-password"
          error={errors.confirmPassword?.message}
          {...register('confirmPassword')}
        />
        <Button type="submit" className="w-full" disabled={isSubmitting}>
          {isSubmitting ? 'Creating account…' : 'Create account'}
        </Button>
      </form>
    </AuthCard>
  )
}
