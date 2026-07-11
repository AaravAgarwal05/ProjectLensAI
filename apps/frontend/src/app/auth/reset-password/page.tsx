'use client'

import { motion } from 'framer-motion'
import Link from 'next/link'
import { Icon } from '@/components/shared/icon'
import { useState } from 'react'

/* ─── animation helpers ─── */

const fadeUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.45, ease: 'easeOut' as const },
}

const stagger = {
  animate: { transition: { staggerChildren: 0.07 } },
}

/* ─── page ─── */

export default function ResetPasswordPage() {
  const [newPwd, setNewPwd] = useState('')
  const [confirmPwd, setConfirmPwd] = useState('')
  const [showNew, setShowNew] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)

  const checks = {
    length: newPwd.length >= 8,
    symbol: /[!@#$%^&*(),.?":{}|<>]/.test(newPwd),
    number: /[0-9]/.test(newPwd),
    upper: /[A-Z]/.test(newPwd),
  }

  const score = Object.values(checks).filter(Boolean).length * 25

  const strengthColor =
    score <= 25 ? 'bg-error' : score <= 75 ? 'bg-secondary' : 'bg-primary'

  const matchError = confirmPwd.length > 0 && newPwd !== confirmPwd

  const requirements = [
    { key: 'length' as const, label: '8+ characters' },
    { key: 'symbol' as const, label: 'Special char' },
    { key: 'number' as const, label: 'Number' },
    { key: 'upper' as const, label: 'Uppercase' },
  ]

  return (
    <>
      {/* ─── Top Brand Bar ─── */}
      <motion.header
        className="fixed top-0 left-0 w-full flex items-center h-16 px-xl z-50 bg-transparent"
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: 'easeOut' }}
      >
        <div className="flex items-center gap-sm">
          <Icon fill className="text-primary text-headline-md">lens_blur</Icon>
          <span className="font-display text-headline-md font-extrabold text-primary tracking-tight">ProjectLens AI</span>
        </div>
      </motion.header>

      <motion.div
        className="flex flex-col gap-xl"
        initial="initial"
        animate="animate"
        variants={stagger}
      >
        {/* ─── Reset Card ─── */}
        <motion.div className="glass-card p-xl rounded-xl ai-glow" variants={fadeUp}>
          <div className="flex flex-col gap-sm mb-lg">
            <h1 className="font-headline-lg text-headline-lg text-on-surface">Reset Password</h1>
            <p className="font-body-md text-body-md text-on-surface-variant">
              Security is our priority. Please choose a strong password that you haven&apos;t used before.
            </p>
          </div>

          <form
            className="flex flex-col gap-md"
            onSubmit={(e) => {
              e.preventDefault()
              if (matchError) return
              const btn = e.currentTarget.querySelector('button[type="submit"]') as HTMLButtonElement
              btn.disabled = true
              btn.innerHTML = `<span class="material-symbols-outlined animate-spin text-[18px]">progress_activity</span> Updating...`
            }}
            id="resetForm"
          >
            {/* New Password */}
            <div className="flex flex-col gap-xs">
              <label className="font-label-md text-label-md text-on-surface-variant uppercase tracking-wider" htmlFor="new_password">New Password</label>
              <div className="relative">
                <input
                  id="new_password"
                  type={showNew ? 'text' : 'password'}
                  placeholder="••••••••"
                  required
                  value={newPwd}
                  onChange={(e) => setNewPwd(e.target.value)}
                  className="w-full bg-surface-container-low border border-outline-variant rounded-lg px-md py-sm text-on-surface font-body-md placeholder:text-outline focus:outline-none focus:border-primary focus:shadow-[0_0_0_1px_#c0c1ff,0_0_15px_rgba(192,193,255,0.15)] transition-all"
                />
                <button
                  type="button"
                  onClick={() => setShowNew(!showNew)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-outline-variant hover:text-on-surface transition-colors"
                >
                  <Icon size="14px">{showNew ? 'visibility_off' : 'visibility'}</Icon>
                </button>
              </div>

              {/* Strength Indicator */}
              <div className="mt-sm space-y-sm">
                <div className="h-1 w-full bg-surface-container-high rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-300 ${strengthColor}`}
                    style={{ width: `${newPwd.length > 0 ? score : 0}%` }}
                  />
                </div>
                <div className="grid grid-cols-2 gap-x-md gap-y-xs">
                  {requirements.map((req) => {
                    const met = checks[req.key]
                    return (
                      <div
                        key={req.key}
                        className={`flex items-center gap-xs font-label-md text-label-md transition-colors ${met ? 'text-primary' : 'text-on-surface-variant'}`}
                      >
                        <Icon fill={met} size="16px">check_circle</Icon>
                        {req.label}
                      </div>
                    )
                  })}
                </div>
              </div>
            </div>

            {/* Confirm Password */}
            <div className="flex flex-col gap-xs mt-sm">
              <label className="font-label-md text-label-md text-on-surface-variant uppercase tracking-wider" htmlFor="confirm_password">Confirm New Password</label>
              <div className="relative">
                <input
                  id="confirm_password"
                  type={showConfirm ? 'text' : 'password'}
                  placeholder="••••••••"
                  required
                  value={confirmPwd}
                  onChange={(e) => setConfirmPwd(e.target.value)}
                  className={`w-full bg-surface-container-low border rounded-lg px-md py-sm text-on-surface font-body-md placeholder:text-outline focus:outline-none focus:shadow-[0_0_0_1px_#c0c1ff,0_0_15px_rgba(192,193,255,0.15)] transition-all ${
                    matchError ? 'border-error' : 'border-outline-variant focus:border-primary'
                  }`}
                />
                <button
                  type="button"
                  onClick={() => setShowConfirm(!showConfirm)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-outline-variant hover:text-on-surface transition-colors"
                >
                  <Icon size="14px">{showConfirm ? 'visibility_off' : 'visibility'}</Icon>
                </button>
              </div>
              {matchError && (
                <p className="font-label-md text-label-md text-error">Passwords do not match.</p>
              )}
            </div>

            <button
              type="submit"
              className="mt-lg w-full bg-primary text-on-primary font-headline-md text-headline-md py-md rounded-lg active:scale-95 duration-100 hover:brightness-110 transition-all shadow-lg shadow-primary/20 flex justify-center items-center gap-sm"
            >
              <span>Update Password</span>
              <Icon size="20px">arrow_forward</Icon>
            </button>
          </form>

          <div className="mt-xl flex justify-center">
            <Link
              href="/auth/login"
              className="font-body-md text-body-md text-primary hover:text-on-primary-container transition-colors flex items-center gap-xs"
            >
              <Icon size="14px">arrow_back</Icon>
              Back to login
            </Link>
          </div>
        </motion.div>

        {/* ─── Encryption Status ─── */}
        <motion.div
          className="glass-card p-md rounded-lg border-outline-variant/30 flex items-center justify-between opacity-80"
          variants={fadeUp}
        >
          <div className="flex items-center gap-sm">
            <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
            <span className="font-code-sm text-code-sm text-on-surface-variant">ENCRYPTION: AES-256 ACTIVE</span>
          </div>
          <span className="font-code-sm text-code-sm text-primary">v2.4.0-stable</span>
        </motion.div>
      </motion.div>

      {/* ─── Footer ─── */}
      <motion.p
        className="fixed bottom-gutter w-full text-center pointer-events-none"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.4, delay: 0.3 }}
      >
        <span className="font-label-md text-label-md text-outline-variant">
          &copy; 2024 ProjectLens Intelligence Systems. All rights reserved.
        </span>
      </motion.p>
    </>
  )
}
