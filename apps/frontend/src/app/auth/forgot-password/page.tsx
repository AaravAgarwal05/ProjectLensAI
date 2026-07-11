'use client'

import { motion } from 'framer-motion'
import Link from 'next/link'
import { Icon } from '@/components/shared/icon'

/* ─── animation helpers ─── */

const fadeUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.45, ease: 'easeOut' as const },
}

const stagger = {
  animate: { transition: { staggerChildren: 0.08 } },
}

/* ─── page ─── */

export default function ForgotPasswordPage() {
  return (
    <motion.div
      className="flex flex-col"
      initial="initial"
      animate="animate"
      variants={stagger}
    >
      {/* ─── Brand ─── */}
      <motion.div className="flex flex-col items-center mb-xl" variants={fadeUp}>
        <div className="w-12 h-12 bg-primary-container/20 rounded-xl flex items-center justify-center mb-md border border-primary/20 ai-glow">
          <Icon fill size="28px" className="text-primary">insights</Icon>
        </div>
        <h1 className="font-display text-headline-lg text-on-surface tracking-tight mb-xs">ProjectLens AI</h1>
        <p className="font-body-md text-on-surface-variant text-center px-lg">Precision Intelligence for your data ecosystem.</p>
      </motion.div>

      {/* ─── Forgot Password Card ─── */}
      <motion.div className="glass-card rounded-xl p-xl ai-glow" variants={fadeUp}>
        <div className="mb-lg">
          <h2 className="font-headline-md text-on-surface mb-xs">Forgot Password?</h2>
          <p className="font-body-md text-on-surface-variant">Enter your registered email to receive a secure recovery link.</p>
        </div>

        <form className="space-y-md" id="forgotPasswordForm" onSubmit={(e) => e.preventDefault()}>
          {/* Email */}
          <div className="space-y-xs">
            <label className="font-label-md text-on-surface-variant flex items-center gap-xs" htmlFor="email">
              <Icon size="16px">mail</Icon>
              EMAIL ADDRESS
            </label>
            <div className="relative group">
              <input
                id="email"
                type="email"
                placeholder="name@company.com"
                required
                className="w-full bg-surface-container-lowest border border-outline-variant rounded-lg px-md py-sm font-body-md text-on-surface placeholder:text-outline focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary transition-all duration-200"
              />
            </div>
          </div>

          {/* Submit */}
          <button
            type="submit"
            className="w-full bg-primary text-on-primary font-headline-md py-sm rounded-lg hover:bg-primary-container transition-all duration-200 active:scale-[0.98] flex items-center justify-center gap-sm mt-lg"
          >
            <span>Send Reset Link</span>
            <Icon size="18px">arrow_forward</Icon>
          </button>
        </form>

        {/* Back to Login */}
        <div className="mt-xl flex justify-center">
          <Link
            href="/auth/login"
            className="font-label-md text-on-surface-variant hover:text-primary transition-colors flex items-center gap-xs group"
          >
            <Icon className="transition-transform group-hover:-translate-x-1" size="16px">arrow_back</Icon>
            Back to Login
          </Link>
        </div>
      </motion.div>

      {/* ─── System Status ─── */}
      <motion.div className="mt-xl flex flex-col items-center gap-sm" variants={fadeUp}>
        <div className="flex items-center gap-md">
          <span className="font-code-sm text-outline px-sm border-r border-outline-variant">SYSTEM V2.4</span>
          <span className="font-code-sm text-outline">SECURE AUTH</span>
        </div>
        <div className="w-16 h-px bg-gradient-to-r from-transparent via-outline-variant to-transparent" />
      </motion.div>
    </motion.div>
  )
}
