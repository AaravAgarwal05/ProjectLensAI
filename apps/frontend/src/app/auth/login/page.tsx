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

export default function LoginPage() {
  return (
    <motion.div
      className="flex flex-col"
      initial="initial"
      animate="animate"
      variants={stagger}
    >
      {/* ─── Brand Identity ─── */}
      <motion.div className="flex flex-col items-center mb-xl" variants={fadeUp}>
        <div className="w-12 h-12 bg-primary flex items-center justify-center rounded-xl mb-md ai-glow">
          <Icon fill size="28px" className="text-on-primary">precision_manufacturing</Icon>
        </div>
        <h1 className="font-display text-headline-lg text-on-surface tracking-tight">ProjectLens AI</h1>
        <p className="font-label-md text-label-md text-on-surface-variant uppercase tracking-widest mt-xs">Precision Intelligence</p>
      </motion.div>

      {/* ─── Login Card ─── */}
      <motion.div className="glass-card rounded-xl p-xl ai-glow shadow-2xl" variants={fadeUp}>
        <form className="space-y-md" onSubmit={(e) => e.preventDefault()}>
          {/* Email */}
          <div className="space-y-sm">
            <label className="font-label-md text-label-md text-on-surface-variant block" htmlFor="email">EMAIL ADDRESS</label>
            <div className="relative group">
              <Icon className="absolute left-md top-1/2 -translate-y-1/2 text-outline group-focus-within:text-primary transition-colors" size="18px">alternate_email</Icon>
              <input
                id="email"
                type="email"
                placeholder="name@company.com"
                className="w-full bg-black border border-outline-variant rounded-lg py-md pl-[44px] pr-md text-on-surface placeholder:text-outline/50 focus:outline-none focus:border-primary transition-all duration-200 input-glow"
              />
            </div>
          </div>

          {/* Password */}
          <div className="space-y-sm">
            <div className="flex justify-between items-center">
              <label className="font-label-md text-label-md text-on-surface-variant block" htmlFor="password">PASSWORD</label>
              <Link href="/auth/forgot-password" className="font-label-md text-label-md text-primary hover:text-primary-fixed-dim transition-colors">Forgot password?</Link>
            </div>
            <div className="relative group">
              <Icon className="absolute left-md top-1/2 -translate-y-1/2 text-outline group-focus-within:text-primary transition-colors" size="18px">lock</Icon>
              <input
                id="password"
                type="password"
                placeholder="••••••••"
                className="w-full bg-black border border-outline-variant rounded-lg py-md pl-[44px] pr-md text-on-surface placeholder:text-outline/50 focus:outline-none focus:border-primary transition-all duration-200 input-glow"
              />
            </div>
          </div>

          {/* Remember me */}
          <div className="flex items-center gap-sm">
            <input
              id="remember"
              type="checkbox"
              className="w-4 h-4 rounded-sm bg-black border-outline-variant text-primary focus:ring-0 focus:ring-offset-0 cursor-pointer"
            />
            <label className="font-body-md text-body-md text-on-surface-variant cursor-pointer select-none" htmlFor="remember">Remember me for 30 days</label>
          </div>

          {/* Sign In */}
          <button
            type="submit"
            className="w-full bg-primary text-on-primary font-headline-md text-headline-md py-md rounded-lg active:scale-95 transition-transform duration-100 hover:bg-primary-fixed-dim shadow-lg shadow-primary/10"
          >
            Sign In
          </button>

          {/* Divider */}
          <div className="relative py-md flex items-center">
            <div className="flex-grow border-t border-outline-variant/30" />
            <span className="flex-shrink mx-md font-label-md text-label-md text-outline/50">OR CONTINUE WITH</span>
            <div className="flex-grow border-t border-outline-variant/30" />
          </div>

          {/* Google */}
          <button
            type="button"
            className="w-full bg-surface-container-low border border-outline-variant rounded-lg py-md flex items-center justify-center gap-md hover:bg-surface-container-high transition-colors text-on-surface font-body-md"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 12-4.53z" fill="#EA4335" />
            </svg>
            Login with Google
          </button>
        </form>
      </motion.div>

      {/* ─── Footer ─── */}
      <motion.p
        className="text-center mt-xl font-body-md text-on-surface-variant"
        variants={fadeUp}
      >
        Don&apos;t have an account?{' '}
        <Link href="/auth/register" className="text-primary font-bold hover:underline underline-offset-4 decoration-2">Create an account</Link>
      </motion.p>
    </motion.div>
  )
}
