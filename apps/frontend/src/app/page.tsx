'use client'

import { useRef } from 'react'
import Link from 'next/link'
import { ArrowRight } from 'lucide-react'
import { motion, useInView } from 'framer-motion'

/* ─── Reusable animation variants ─── */
const fadeUp = {
  hidden: { opacity: 0, y: 24 },
  visible: (i = 0) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.12, duration: 0.6, ease: [0.21, 0.47, 0.32, 0.98] as const },
  }),
}

const stagger = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1, delayChildren: 0.15 },
  },
}

function FadeInSection({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  const ref = useRef(null)
  const isInView = useInView(ref, { once: true, margin: '-80px' })
  return (
    <motion.div
      ref={ref}
      initial="hidden"
      animate={isInView ? 'visible' : 'hidden'}
      variants={stagger}
      className={className}
    >
      {children}
    </motion.div>
  )
}

/* ─── Integration data ─── */
const integrations = [
  { name: 'PostgreSQL', color: 'bg-blue-500' },
  { name: 'Chroma', color: 'bg-yellow-500' },
  { name: 'Ollama', color: 'bg-zinc-100' },
  { name: 'Vercel AI', color: 'bg-white' },
]

/* ─── Footer link columns ─── */
const footerGroups = [
  {
    title: 'Product',
    links: ['Platform', 'Neural Search', 'Pricing', 'API Docs'],
  },
  { title: 'Company', links: ['About', 'Changelog', 'Careers', 'Privacy'] },
  { title: 'Resources', links: ['Community', 'Case Studies', 'Tutorials', 'Support'] },
]

export default function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col bg-surface-bg text-zinc-100">

      {/* ═══════════════ STICKY NAV ═══════════════ */}
      <motion.nav
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: 'easeOut' }}
        className="fixed top-0 z-50 w-full border-b border-surface-border bg-surface-card/60 backdrop-blur-lg"
      >
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          {/* Logo */}
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded bg-brand">
              <svg className="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} />
                <path d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} />
              </svg>
            </div>
            <span className="text-lg font-bold tracking-tight">ProjectLens AI</span>
          </div>

          {/* Desktop nav */}
          <div className="hidden items-center gap-8 text-sm font-medium text-zinc-400 md:flex">
            <a href="#" className="transition-colors hover:text-white">Docs</a>
            <a href="#" className="transition-colors hover:text-white">Pricing</a>
            <a href="#features" className="transition-colors hover:text-white">Workflows</a>
            <a href="#" className="transition-colors hover:text-white">Enterprise</a>
          </div>

          {/* Auth */}
          <div className="flex items-center gap-4">
            <Link href="/auth/login" className="px-4 py-2 text-sm font-medium text-zinc-400 transition-colors hover:text-white">
              Sign In
            </Link>
            <Link
              href="/auth/register"
              className="rounded-lg bg-brand px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-brand/20 transition-all hover:bg-brand-dark"
            >
              Sign Up
            </Link>
          </div>
        </div>
      </motion.nav>

      {/* ═══════════════ HERO ═══════════════ */}
      <header className="relative overflow-hidden pt-32 pb-20 lg:pt-48 lg:pb-32">
        {/* Grid background */}
        <div
          className="absolute inset-0 z-[-2]"
          style={{
            backgroundImage:
              'linear-gradient(to right, #18181b 1px, transparent 1px), linear-gradient(to bottom, #18181b 1px, transparent 1px)',
            backgroundSize: '40px 40px',
            maskImage: 'radial-gradient(ellipse 60% 50% at 50% 0%, #000 70%, transparent 100%)',
            WebkitMaskImage: 'radial-gradient(ellipse 60% 50% at 50% 0%, #000 70%, transparent 100%)',
          }}
        />
        {/* Glow */}
        <div
          className="absolute left-1/2 top-[-100px] z-[-1] h-[500px] w-[500px] -translate-x-1/2"
          style={{
            background: 'radial-gradient(circle, rgba(99, 102, 241, 0.15) 0%, transparent 70%)',
            filter: 'blur(60px)',
          }}
        />

        <div className="mx-auto max-w-7xl px-4 text-center sm:px-6 lg:px-8">
          {/* Live badge */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.5 }}
            className="mb-6 inline-flex items-center gap-2 rounded-full border border-brand/30 bg-brand/10 px-3 py-1 text-xs font-semibold text-brand"
          >
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-brand opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-brand" />
            </span>
            V2.0 Engine Now Live
          </motion.div>

          {/* Heading */}
          <motion.h1
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.35, duration: 0.7, ease: [0.21, 0.47, 0.32, 0.98] as const }}
            className="mb-6 bg-gradient-to-b from-white to-zinc-500 bg-clip-text text-5xl font-bold tracking-tight text-transparent lg:text-7xl"
          >
            Precision Intelligence for <br className="hidden lg:block" />
            your Data Ecosystem.
          </motion.h1>

          {/* Subtitle */}
          <motion.p
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5, duration: 0.6 }}
            className="mx-auto mb-10 max-w-2xl text-lg text-zinc-400"
          >
            Deep-source analysis, comparative intelligence, and multi-vector neural search.
            Built for developers who require deterministic insights from stochastic systems.
          </motion.p>

          {/* CTA buttons */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.65, duration: 0.5 }}
            className="mb-16 flex flex-col items-center justify-center gap-4 sm:flex-row"
          >
            <Link
              href="/auth/register"
              className="flex items-center gap-2 rounded-xl bg-brand px-8 py-4 font-bold text-white shadow-lg shadow-brand/20 transition-all hover:bg-brand-dark"
            >
              Start Free Trial
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="#features"
              className="flex items-center gap-2 rounded-xl border border-zinc-700 px-8 py-4 font-bold text-white transition-all hover:bg-zinc-800"
            >
              <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z" /></svg>
              Watch Demo
            </Link>
          </motion.div>

          {/* Dashboard Mockup */}
          <motion.div
            initial={{ opacity: 0, y: 32 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.85, duration: 0.7, ease: [0.21, 0.47, 0.32, 0.98] as const }}
            className="group relative mx-auto max-w-6xl"
          >
            {/* Glow border */}
            <div className="absolute -inset-1 rounded-2xl bg-gradient-to-r from-brand to-purple-600 opacity-20 blur transition duration-1000 group-hover:opacity-30" />

            <div className="dashboard-mockup relative overflow-hidden rounded-xl border border-zinc-800 bg-surface-bg"
                 style={{ boxShadow: '0 0 50px -10px rgba(99, 102, 241, 0.3)' }}>
              {/* Dashboard screenshot */}
              <img
                alt="ProjectLens Dashboard UI"
                className="w-full h-auto opacity-90"
                src="https://lh3.googleusercontent.com/aida-public/AB6AXuA0kbLc3SnMhjwiWCgwxYoBSFwne3u9PWdTYSUWiJJK7OptE1N9NeazFmPh7gLUOs1NEES6OkXI7PBgHDlZkfeMcJBHsCDolqLrtcBR1ZRdoYDjg7Ra3FiwHAoaA3QbyiuZB4nZRr9zMxuiz7c_uNxa1xAjC-lLlDRrIRPkKoA8CJdxdYmLnvv6DMckMAT0APMBYJTAtAPMErmxZNMpiKbwKPIZyft5h8rqr6c6iGeEaD87yqGiM6szP0nxJMHMcnQLuXcJGpv5Wdlo"
              />

              {/* Neural Architecture overlay */}
              <div
                className="absolute left-8 top-8 hidden rounded-lg border border-white/10 p-4 backdrop-blur-lg lg:block"
                style={{ background: 'rgba(23, 23, 23, 0.6)' }}
              >
                <div className="mb-2 text-xs text-zinc-500">Neural Architecture</div>
                <div className="font-mono text-xl text-brand">System Nominal</div>
              </div>
            </div>
          </motion.div>
        </div>
      </header>

      {/* ═══════════════ INTEGRATIONS BAR ═══════════════ */}
      <section className="border-y border-zinc-800 bg-surface-bg/50 py-12">
        <FadeInSection className="mx-auto max-w-7xl px-4">
          <motion.p
            variants={fadeUp}
            className="mb-8 text-center text-xs font-semibold uppercase tracking-widest text-zinc-500"
          >
            Seamless Integration with the AI Stack
          </motion.p>
          <motion.div
            variants={fadeUp}
            className="flex flex-wrap items-center justify-center gap-8 opacity-50 grayscale transition-all duration-500 hover:grayscale-0 md:gap-16"
          >
            {integrations.map((i) => (
              <span key={i.name} className="flex items-center gap-2 text-lg font-bold">
                <span className={`h-2 w-2 rounded-full ${i.color}`} />
                {i.name}
              </span>
            ))}
          </motion.div>
        </FadeInSection>
      </section>

      {/* ═══════════════ FEATURES BENTO GRID ═══════════════ */}
      <section id="features" className="mx-auto max-w-7xl px-4 py-24 sm:px-6 lg:px-8">
        <FadeInSection>
          <motion.h2 variants={fadeUp} className="mb-4 text-3xl font-bold">
            Engineered for Analysis
          </motion.h2>
          <motion.p variants={fadeUp} className="mb-16 text-zinc-400">
            Tools that extend the boundaries of what your data can tell you.
          </motion.p>
        </FadeInSection>

        <div className="grid grid-cols-1 gap-6 md:grid-cols-12">
          {/* ─── Comparative Intelligence (col-span-8) ─── */}
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-60px' }}
            transition={{ duration: 0.6, ease: [0.21, 0.47, 0.32, 0.98] as const }}
            className="group col-span-12 overflow-hidden rounded-3xl border border-surface-border bg-surface-card p-8 transition-colors hover:border-brand/50 md:col-span-8"
          >
            <div className="flex h-full flex-col">
              <div className="mb-8">
                <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-brand/10 text-brand">
                  <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} />
                  </svg>
                </div>
                <h3 className="mb-2 text-2xl font-bold">Comparative Intelligence</h3>
                <p className="text-zinc-400">
                  Select Report A. Select Report B. Find Divergence instantly across thousands of variables.
                </p>
              </div>
              <div className="mt-auto flex items-center gap-4 border-t border-zinc-800 pt-6">
                <span className="flex items-center rounded border border-brand/20 bg-brand/5 px-4 py-2 font-mono text-xs text-brand">
                  Neural-Sync v4.2
                </span>
                <span className="text-brand">↔</span>
                <span className="flex items-center rounded border border-zinc-700 bg-zinc-900 px-4 py-2 font-mono text-xs text-zinc-500">
                  Synapse-Prime R7
                </span>
              </div>
            </div>
          </motion.div>

          {/* ─── Deep Citation (col-span-4) ─── */}
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-60px' }}
            transition={{ duration: 0.6, delay: 0.1, ease: [0.21, 0.47, 0.32, 0.98] as const }}
            className="group col-span-12 overflow-hidden rounded-3xl border border-surface-border bg-surface-card p-8 transition-colors hover:border-brand/50 md:col-span-4"
          >
            <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-brand/10 text-brand">
              <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} />
              </svg>
            </div>
            <h3 className="mb-2 text-xl font-bold">Deep Citation</h3>
            <p className="text-sm text-zinc-400">
              Every answer is a link to the source. No hallucinations, only validated references.
            </p>
            <div className="mt-6 rounded-lg border border-zinc-800 bg-zinc-900/50 p-3 font-mono text-[10px] text-brand">
              [Ref: Q3_Analysis_Final.pdf - p.42]
            </div>
          </motion.div>

          {/* ─── Multi-Vector Search (col-span-12) ─── */}
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-60px' }}
            transition={{ duration: 0.6, delay: 0.2, ease: [0.21, 0.47, 0.32, 0.98] as const }}
            className="group relative col-span-12 overflow-hidden rounded-3xl border border-surface-border bg-surface-card p-8 transition-colors hover:border-brand/50"
          >
            <div className="grid items-center gap-8 md:grid-cols-2">
              <div>
                <h3 className="mb-4 text-2xl font-bold">Multi-Vector Search</h3>
                <p className="text-zinc-400">
                  Hybrid retrieval across all your documentation. Semantic context combined with
                  keyword precision to find the &ldquo;needle in the haystack&rdquo; every time.
                </p>
                <ul className="mt-6 space-y-3">
                  {['Hierarchical Document Indexing', 'Context-Aware Chunking'].map((b) => (
                    <li key={b} className="flex items-center gap-3 text-sm text-zinc-300">
                      <svg className="h-5 w-5 text-brand" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path d="M5 13l4 4L19 7" strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} />
                      </svg>
                      {b}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Bar chart visualization */}
              <div className="relative flex h-48 items-center justify-center rounded-xl border border-zinc-800 bg-zinc-900">
                <div
                  className="absolute inset-0 opacity-20"
                  style={{
                    backgroundImage:
                      'linear-gradient(to right, #18181b 1px, transparent 1px), linear-gradient(to bottom, #18181b 1px, transparent 1px)',
                    backgroundSize: '40px 40px',
                  }}
                />
                <div className="flex items-end gap-1">
                  {[12, 16, 8, 20, 14, 18, 10, 22, 15].map((h, i) => (
                    <div
                      key={i}
                      className="w-1 animate-pulse rounded-t bg-brand"
                      style={{ height: `${h * 4}px`, animationDelay: `${i * 100}ms` }}
                    />
                  ))}
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* ═══════════════ CTA ═══════════════ */}
      <section className="relative overflow-hidden py-24">
        {/* Bottom glow */}
        <div
          className="absolute bottom-[-200px] left-1/2 z-[-1] h-[500px] w-[500px] -translate-x-1/2 opacity-30"
          style={{
            background: 'radial-gradient(circle, rgba(99, 102, 241, 0.15) 0%, transparent 70%)',
            filter: 'blur(60px)',
          }}
        />

        <FadeInSection className="mx-auto max-w-4xl border-t border-zinc-800 px-4 pt-24 text-center">
          <motion.h2 variants={fadeUp} className="mb-6 text-4xl font-bold">
            Ready to lens your data?
          </motion.h2>
          <motion.p variants={fadeUp} className="mb-10 text-lg text-zinc-400">
            Join 2,000+ teams using ProjectLens to drive precision in their intelligence workflows.
          </motion.p>
          <motion.div variants={fadeUp} className="flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Link
              href="/auth/register"
              className="rounded-xl bg-brand px-10 py-4 font-bold text-white shadow-xl shadow-brand/20 transition-all hover:bg-brand-dark"
            >
              Get Started Now
            </Link>
            <Link
              href="#features"
              className="rounded-xl border border-zinc-700 px-10 py-4 font-bold text-white transition-all hover:bg-zinc-800"
            >
              Contact Sales
            </Link>
          </motion.div>
        </FadeInSection>
      </section>

      {/* ═══════════════ FOOTER ═══════════════ */}
      <footer className="border-t border-zinc-800 bg-surface-bg px-4 pb-10 pt-20 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl">
          <div className="mb-16 grid grid-cols-2 gap-8 md:grid-cols-4 lg:grid-cols-5">
            {/* Brand */}
            <div className="col-span-2 lg:col-span-2">
              <div className="mb-6 flex items-center gap-2">
                <div className="flex h-6 w-6 items-center justify-center rounded bg-brand">
                  <svg className="h-4 w-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} />
                    <path d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} />
                  </svg>
                </div>
                <span className="font-bold tracking-tight">ProjectLens AI</span>
              </div>
              <p className="mb-6 max-w-xs text-sm text-zinc-500">
                Next-generation intelligence analysis for technical teams and data scientists. Precision at scale.
              </p>
              <div className="flex gap-4">
                {/* Twitter/X */}
                <a href="#" className="text-zinc-500 transition-colors hover:text-white">
                  <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M24 4.557c-.883.392-1.832.656-2.828.775 1.017-.609 1.798-1.574 2.165-2.724-.951.564-2.005.974-3.127 1.195-.897-.957-2.178-1.555-3.594-1.555-3.179 0-5.515 2.966-4.797 6.045-4.091-.205-7.719-2.165-10.148-5.144-1.29 2.213-.669 5.108 1.523 6.574-.806-.026-1.566-.247-2.229-.616-.054 2.281 1.581 4.415 3.949 4.89-.693.188-1.452.232-2.224.084.626 1.956 2.444 3.379 4.6 3.419-2.07 1.623-4.678 2.348-7.29 2.04 2.179 1.397 4.768 2.212 7.548 2.212 9.142 0 14.307-7.721 13.995-14.646.962-.695 1.797-1.562 2.457-2.549z" />
                  </svg>
                </a>
                {/* GitHub */}
                <a href="#" className="text-zinc-500 transition-colors hover:text-white">
                  <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
                  </svg>
                </a>
              </div>
            </div>

            {/* Link columns */}
            {footerGroups.map((g) => (
              <div key={g.title}>
                <h4 className="mb-4 text-sm font-semibold text-white">{g.title}</h4>
                <ul className="space-y-2 text-sm text-zinc-500">
                  {g.links.map((l) => (
                    <li key={l}>
                      <a href="#" className="transition-colors hover:text-brand">{l}</a>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          {/* Bottom bar */}
          <div className="flex flex-col items-center justify-between gap-4 border-t border-zinc-900 pt-10 md:flex-row">
            <p className="text-xs text-zinc-600">
              &copy; {new Date().getFullYear()} ProjectLens AI. All rights reserved.
            </p>
            <div className="flex gap-4 text-xs text-zinc-600">
              {['Security', 'Terms', 'Cookies'].map((l) => (
                <a key={l} href="#" className="transition-colors hover:text-white">{l}</a>
              ))}
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
