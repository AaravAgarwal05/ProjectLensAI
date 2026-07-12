'use client'

import Link from 'next/link'
import { motion } from 'framer-motion'

/* ─── glass-card styles (inline so no shared import needed) ─── */

const glassCard =
  'bg-[rgba(9,9,11,0.8)] backdrop-blur-[20px] border border-[rgba(39,39,42,0.5)] relative overflow-hidden'
const glassCardPseudo =
  "before:content-[''] before:absolute before:inset-0 before:p-[1px] before:rounded-inherit before:bg-gradient-to-br before:from-[rgba(192,193,255,0.2)] before:to-[rgba(221,183,255,0.05)] before:[mask:linear-gradient(#fff_0_0)_content-box,linear-gradient(#fff_0_0)] before:[mask-composite:exclude] before:pointer-events-none"
const aiGlow = 'shadow-[0_0_40px_5px_rgba(192,193,255,0.15)]'

/* ─── floating animation ─── */

const floatVariants = {
  animate: {
    y: [0, -20, 0],
    transition: { duration: 6, repeat: Infinity, ease: 'easeInOut' as const },
  },
}

/* ─── orbit ring spin ─── */

const orbitVariants = {
  animate: {
    rotate: 360,
    transition: { duration: 10, repeat: Infinity, ease: 'linear' as const },
  },
}

const orbitReverseVariants = {
  animate: {
    rotate: -360,
    transition: { duration: 15, repeat: Infinity, ease: 'linear' as const },
  },
}

/* ─── particles ─── */

const fadeInPulse = {
  initial: { opacity: 0, scale: 0.9 },
  animate: {
    opacity: 1,
    scale: 1,
    transition: { duration: 0.6 },
  },
}

/* ─── grid background ─── */

const gridBg =
  '[background-image:linear-gradient(to_right,#18181b_1px,transparent_1px),linear-gradient(to_bottom,#18181b_1px,transparent_1px)] [background-size:40px_40px]'

export default function NotFound() {
  return (
    <div className="relative min-h-screen bg-background text-on-surface font-body-md overflow-hidden selection:bg-primary/30">
      {/* ─── Ambient Grid ─── */}
      <div className={`fixed inset-0 ${gridBg} opacity-30 pointer-events-none`} />
      <div className="fixed inset-0 bg-gradient-to-t from-background via-transparent to-background pointer-events-none" />

      {/* ─── Main Content ─── */}
      <main className="relative min-h-screen flex flex-col items-center justify-center p-md text-center">
        {/* Large ghost 404 */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 opacity-[0.03] select-none pointer-events-none">
          <h1 className="text-[40vw] font-black leading-none tracking-tighter">404</h1>
        </div>

        {/* ─── Visual Content ─── */}
        <motion.div
          className="z-10 flex flex-col items-center max-w-2xl"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.7 }}
        >
          {/* AI Orbiting Animation */}
          <motion.div
            className="relative w-64 h-64 md:w-80 md:h-80 mb-xl"
            variants={floatVariants}
            animate="animate"
          >
            {/* Outer orbit */}
            <motion.div
              className="absolute inset-0 rounded-full border border-primary/20"
              variants={orbitVariants}
              animate="animate"
            />
            {/* Inner reverse orbit */}
            <motion.div
              className="absolute inset-4 rounded-full border border-secondary/10"
              variants={orbitReverseVariants}
              animate="animate"
            />

            {/* Central eye / lens */}
            <div className="absolute inset-0 flex items-center justify-center">
              <div
                className={`w-48 h-48 md:w-56 md:h-56 rounded-full flex items-center justify-center ${glassCard} ${glassCardPseudo} ${aiGlow} border border-primary/30 overflow-hidden`}
              >
                {/* Scan line */}
                <motion.div
                  className="absolute w-full h-[2px] bg-gradient-to-r from-transparent via-primary/30 to-transparent"
                  animate={{ top: ['-2px', '100%'] }}
                  transition={{ duration: 4, repeat: Infinity, ease: 'linear' }}
                />
                <img
                  className="w-32 h-32 md:w-40 md:h-40 opacity-80 mix-blend-screen"
                  src="https://lh3.googleusercontent.com/aida-public/AB6AXuAkasmgBzJtRcVWqml9ctvVhSmkJK3ifi_CbUZwO9usGS78_fMVIzjQVF9AkfF3U9G16VeC4LD7T1tLOrDW7aUQc0V7xiV-bSTjO1Hj915S4Wjn7lsb1TxrZ4_CDEQY5MyS-E4w6eqr9r8nDeAL92cHcMDXy9gFMm_cJYjwSGQA5Ilc5mlVp4vmghaiCDE2SvcFTk7qjVGSbavzotUq77HfogpBxNF7SCW49WqyI2HegyVR9z5cBXY8cvO9YfrAngMMWd5pKRgWXpDH"
                  alt="Fractured AI lens icon with glowing violet circuitry"
                />
              </div>
            </div>

            {/* Floating data particles */}
            <motion.div
              className="absolute top-0 right-0 p-2 rounded-xl text-label-md border border-outline-variant/30"
              style={{ background: 'rgba(9,9,11,0.8)', backdropFilter: 'blur(20px)' }}
              variants={fadeInPulse}
              animate="animate"
            >
              <span className="text-primary mr-1">ERR_CODE:</span> NULL_REF_OBJECT
            </motion.div>

            <motion.div
              className="absolute bottom-10 left-0 p-2 rounded-xl text-label-md border border-outline-variant/30"
              style={{ background: 'rgba(9,9,11,0.8)', backdropFilter: 'blur(20px)' }}
              variants={fadeInPulse}
              animate="animate"
              transition={{ delay: 0.3 }}
            >
              <span className="text-secondary mr-1">COORD:</span> 0x000F4
            </motion.div>
          </motion.div>

          {/* Error Message */}
          <motion.h2
            className="font-display text-headline-lg mb-md text-on-surface"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.45 }}
          >
            Analysis Lost in Space.
          </motion.h2>
          <motion.p
            className="font-body-md text-on-surface-variant max-w-md mb-xl leading-relaxed"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.45, duration: 0.45 }}
          >
            The neural pathway for this request has been terminated. The page you
            are looking for does not exist in our current model.
          </motion.p>

          {/* Actions */}
          <motion.div
            className="flex flex-col sm:flex-row gap-md"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6, duration: 0.45 }}
          >
            <Link
              href="/dashboard"
              className="inline-flex items-center justify-center gap-2 bg-primary text-on-primary px-lg py-3 rounded-xl font-bold text-body-md hover:bg-primary-container hover:text-on-primary-container transition-all active:scale-95 group"
            >
              <span className="material-symbols-outlined text-body-md">dashboard</span>
              Back to Dashboard
            </Link>
            <button
              onClick={() => window.history.back()}
              className="inline-flex items-center justify-center gap-2 bg-surface-container border border-outline-variant text-on-surface px-lg py-3 rounded-xl font-medium text-body-md hover:bg-surface-bright/20 transition-all active:scale-95"
            >
              <span className="material-symbols-outlined text-body-md">arrow_back</span>
              Return to Previous
            </button>
          </motion.div>

          {/* Terminal-style Debug Footer */}
          <motion.div
            className="mt-24 font-code-sm text-code-sm text-outline opacity-50 flex gap-lg"
            initial={{ opacity: 0 }}
            animate={{ opacity: 0.5 }}
            transition={{ delay: 0.8, duration: 0.45 }}
          >
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-error" />
              <span>System Status: Anomalous</span>
            </div>
            <div className="hidden sm:block">
              <span>ProjectLens Build v2.4.0-Stable</span>
            </div>
            <div className="hidden sm:block">
              <span>Lat: 40.7128° N, Long: 74.0060° W</span>
            </div>
          </motion.div>
        </motion.div>
      </main>
    </div>
  )
}
