'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { Icon } from '@/components/shared/icon'
import { AuthService } from '@/services/auth'

/* ─── animation helpers ─── */

const fadeUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.45, ease: 'easeOut' as const },
}

const stagger = {
  animate: { transition: { staggerChildren: 0.07 } },
}

/* ─── roles ─── */

const roles = [
  { value: 'Student', icon: 'school' as const, label: 'Student' },
  { value: 'Teacher', icon: 'workspace_premium' as const, label: 'Teacher' },
]

/* ─── validation ─── */

interface FieldErrors {
  name?: string
  email?: string
  password?: string
  terms?: string
}

function validateName(v: string): string | undefined {
  if (!v.trim()) return 'Name is required'
  if (v.trim().length < 2) return 'Name must be at least 2 characters'
  return undefined
}

function validateEmail(v: string): string | undefined {
  if (!v.trim()) return 'Email is required'
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)) return 'Enter a valid email address'
  return undefined
}

function validatePassword(v: string): string | undefined {
  if (!v) return 'Password is required'
  if (v.length < 8) return 'Password must be at least 8 characters'
  return undefined
}

/* ─── page ─── */

export default function RegisterPage() {
  const router = useRouter()

  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState('Student')
  const [agreed, setAgreed] = useState(false)
  const [loading, setLoading] = useState(false)
  const [errors, setErrors] = useState<FieldErrors>({})
  const [apiError, setApiError] = useState('')

  function validate(): FieldErrors {
    return {
      name: validateName(name),
      email: validateEmail(email),
      password: validatePassword(password),
      terms: agreed ? undefined : 'You must agree to the terms',
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setApiError('')

    const fieldErrors = validate()
    setErrors(fieldErrors)
    if (Object.values(fieldErrors).some(Boolean)) return

    setLoading(true)
    try {
      await AuthService.register(email, password, name)
      router.push('/dashboard')
    } catch (err) {
      setApiError(err instanceof Error ? err.message : 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <motion.div
      className="flex flex-col"
      initial="initial"
      animate="animate"
      variants={stagger}
    >
      {/* ─── Brand ─── */}
      <motion.div className="flex flex-col items-center mb-xl" variants={fadeUp}>
        <div className="w-12 h-12 bg-primary-container rounded-lg flex items-center justify-center mb-md ai-glow">
          <Icon fill size="28px" className="text-on-primary-container font-bold">filter_center_focus</Icon>
        </div>
        <h1 className="font-display text-headline-lg text-primary tracking-tight">ProjectLens AI</h1>
        <p className="font-body-md text-on-surface-variant mt-xs">Precision Intelligence for Educators &amp; Students</p>
      </motion.div>

      {/* ─── Registration Card ─── */}
      <motion.div className="glass-card p-xl rounded-xl ai-glow" variants={fadeUp}>
        <h2 className="font-headline-md text-on-surface mb-lg">Create your account</h2>

        {apiError && (
          <div className="mb-md p-sm bg-error-container/20 border border-error/30 rounded-lg font-body-md text-error text-sm">
            <Icon className="inline mr-xs align-text-bottom" size="16px">error</Icon>
            {apiError}
          </div>
        )}

        <form className="space-y-md" onSubmit={handleSubmit} noValidate>
          {/* Full Name */}
          <div className="space-y-xs group">
            <label className="font-label-md text-label-md text-on-surface-variant group-focus-within:text-primary transition-colors" htmlFor="full_name">Full Name</label>
            <div className={`relative flex items-center border ${errors.name ? 'border-error' : 'border-outline-variant'} bg-black rounded p-sm transition-all focus-within:border-primary focus-within:shadow-[0_0_15px_rgba(128,131,255,0.1)]`}>
              <Icon className="text-outline mr-sm" size="18px">person</Icon>
              <input
                id="full_name"
                name="full_name"
                type="text"
                placeholder="John Doe"
                value={name}
                onChange={(e) => { setName(e.target.value); if (errors.name) setErrors((p) => ({ ...p, name: validateName(e.target.value) })) }}
                className="bg-transparent border-none text-body-md text-on-surface w-full focus:ring-0 placeholder:text-outline/50"
              />
            </div>
            {errors.name && <p className="font-label-md text-error text-xs mt-1">{errors.name}</p>}
          </div>

          {/* Email */}
          <div className="space-y-xs group">
            <label className="font-label-md text-label-md text-on-surface-variant group-focus-within:text-primary transition-colors" htmlFor="email">Email Address</label>
            <div className={`relative flex items-center border ${errors.email ? 'border-error' : 'border-outline-variant'} bg-black rounded p-sm transition-all focus-within:border-primary focus-within:shadow-[0_0_15px_rgba(128,131,255,0.1)]`}>
              <Icon className="text-outline mr-sm" size="18px">mail</Icon>
              <input
                id="email"
                name="email"
                type="email"
                placeholder="john@example.com"
                value={email}
                onChange={(e) => { setEmail(e.target.value); if (errors.email) setErrors((p) => ({ ...p, email: validateEmail(e.target.value) })) }}
                className="bg-transparent border-none text-body-md text-on-surface w-full focus:ring-0 placeholder:text-outline/50"
              />
            </div>
            {errors.email && <p className="font-label-md text-error text-xs mt-1">{errors.email}</p>}
          </div>

          {/* Password */}
          <div className="space-y-xs group">
            <label className="font-label-md text-label-md text-on-surface-variant group-focus-within:text-primary transition-colors" htmlFor="password">Password</label>
            <div className={`relative flex items-center border ${errors.password ? 'border-error' : 'border-outline-variant'} bg-black rounded p-sm transition-all focus-within:border-primary focus-within:shadow-[0_0_15px_rgba(128,131,255,0.1)]`}>
              <Icon className="text-outline mr-sm" size="18px">lock</Icon>
              <input
                id="password"
                name="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => { setPassword(e.target.value); if (errors.password) setErrors((p) => ({ ...p, password: validatePassword(e.target.value) })) }}
                className="bg-transparent border-none text-body-md text-on-surface w-full focus:ring-0 placeholder:text-outline/50"
              />
            </div>
            {errors.password && <p className="font-label-md text-error text-xs mt-1">{errors.password}</p>}
          </div>

          {/* Role Selection */}
          <div className="space-y-xs">
            <span className="font-label-md text-label-md text-on-surface-variant mb-xs block">Choose your role</span>
            <div className="grid grid-cols-2 gap-sm">
              {roles.map((r) => (
                <label key={r.value} className="cursor-pointer group">
                  <input type="radio" name="role" value={r.value} checked={role === r.value} onChange={() => setRole(r.value)} className="hidden peer" />
                  <div className="flex items-center justify-center gap-sm p-sm border border-outline-variant rounded bg-black/50 peer-checked:border-primary peer-checked:bg-primary-container/10 transition-all hover:bg-surface-container-high">
                    <Icon className="text-outline group-hover:text-on-surface peer-checked:text-primary" size="18px">{r.icon}</Icon>
                    <span className="font-label-md text-on-surface-variant peer-checked:text-on-surface">{r.label}</span>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Terms */}
          <div className="flex items-start gap-sm pt-xs">
            <input
              id="terms"
              type="checkbox"
              checked={agreed}
              onChange={(e) => { setAgreed(e.target.checked); if (errors.terms) setErrors((p) => ({ ...p, terms: undefined })) }}
              className="mt-1 rounded bg-black border-outline-variant text-primary focus:ring-primary focus:ring-offset-black"
            />
            <label className="font-body-md text-code-sm text-on-surface-variant" htmlFor="terms">
              I agree to the{' '}
              <Link href="#" className="text-primary hover:underline">Terms of Service</Link> and{' '}
              <Link href="#" className="text-primary hover:underline">Privacy Policy</Link>.
            </label>
          </div>
          {errors.terms && <p className="font-label-md text-error text-xs">{errors.terms}</p>}

          {/* Submit */}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-primary hover:bg-primary-fixed-dim active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed text-on-primary font-headline-md py-sm rounded-lg transition-all ai-glow mt-lg flex items-center justify-center gap-sm"
          >
            {loading ? (
              <>
                <span className="inline-block w-4 h-4 border-2 border-on-primary border-t-transparent rounded-full animate-spin" />
                Creating account…
              </>
            ) : (
              'Create Account'
            )}
          </button>
        </form>

        <div className="mt-lg pt-lg border-t border-outline-variant text-center">
          <p className="font-body-md text-on-surface-variant">
            Already have an account?{' '}
            <Link href="/auth/login" className="text-primary font-bold hover:underline ml-xs transition-colors">Sign in</Link>
          </p>
        </div>
      </motion.div>

      {/* ─── Feature Badges ─── */}
      <motion.div className="mt-xl grid grid-cols-3 gap-sm opacity-60" variants={fadeUp}>
        {[
          { icon: 'bolt' as const, label: 'Real-time', color: 'text-primary' },
          { icon: 'shield' as const, label: 'Secure', color: 'text-secondary' },
          { icon: 'insights' as const, label: 'Smart', color: 'text-tertiary' },
        ].map((f) => (
          <div key={f.label} className="flex flex-col items-center text-center p-sm glass-card rounded-lg">
            <Icon className={`${f.color} mb-xs`} size="16px">{f.icon}</Icon>
            <span className="font-label-md text-[10px] uppercase tracking-widest text-outline">{f.label}</span>
          </div>
        ))}
      </motion.div>

      {/* ─── Footer ─── */}
      <motion.p className="font-label-md text-outline text-center mt-xl" variants={fadeUp}>
        &copy; 2024 ProjectLens AI. All rights reserved.
      </motion.p>
    </motion.div>
  )
}
