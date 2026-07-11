'use client'

import { useState, useRef, useEffect } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { Icon } from '@/components/shared/icon'
import { placeholderChatSessions, placeholderChatMessages } from '@/lib/placeholders'

/* ─── animation variants ─── */

const containerVariants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.07 } },
}

const messageVariants = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.45, ease: 'easeOut' as const } },
}

const sidebarVariants = {
  hidden: { opacity: 0, x: -20 },
  show: { opacity: 1, x: 0, transition: { duration: 0.5, ease: 'easeOut' as const } },
}

const contextPanelVariants = {
  hidden: { opacity: 0, x: 20 },
  show: { opacity: 1, x: 0, transition: { duration: 0.5, delay: 0.15, ease: 'easeOut' as const } },
}

/* ─── Source Card sub-component ─── */

function SourceCard({
  source,
  labelClass,
  badgeClass,
  transitionDelay,
}: {
  source: { label: string; match: string; title: string; content: string; page: string; date: string }
  labelClass: string
  badgeClass: string
  transitionDelay: number
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: transitionDelay }}
      className="glass-card rounded-xl p-md"
    >
      <div className="mb-sm flex items-center justify-between">
        <span className={`font-label-md uppercase ${labelClass}`}>{source.label}</span>
        <span className={`rounded-full ${badgeClass} px-sm py-0.5 font-label-md`}>
          {source.match}
        </span>
      </div>
      <h3 className="font-body-md font-bold text-on-surface">{source.title}</h3>
      <p className="mt-xs line-clamp-3 font-body-md text-on-surface-variant">{source.content}</p>
      <div className="mt-sm flex items-center gap-lg">
        <span className="flex items-center gap-xs font-label-md text-outline">
          <Icon size="14px">description</Icon>
          {source.page}
        </span>
        <span className="flex items-center gap-xs font-label-md text-outline">
          <Icon size="14px">calendar_today</Icon>
          {source.date}
        </span>
      </div>
    </motion.div>
  )
}

/* ─── static data for the chat sidebar ─── */

const todayChats = [
  { id: '1', title: 'Q3 Fiscal Discrepancies', active: true },
  { id: '2', title: 'Market Volatility Analysis', active: false },
]

const yesterdayChats = [
  { id: '3', title: 'Risk Vector Correlation', active: false },
  { id: '4', title: 'User Onboarding Optimization', active: false },
]

const contextSources = [
  {
    id: 's1',
    label: 'Report Segment',
    match: '98% Match',
    title: 'Q3 Financial Summary',
    content:
      'Total operating expenses for the quarter ended September 30, 2023, were $145.2M, compared to $127.8M in the prior quarter...',
    page: 'Page 24',
    date: 'Oct 12, 2023',
    borderColor: 'border-l-primary',
    badgeBg: 'bg-primary/10 text-primary',
  },
  {
    id: 's2',
    label: 'Strategic Deck',
    match: '84% Match',
    title: 'Growth Trajectory Model',
    content:
      'Projected revenue growth trajectory shows a 14.2% acceleration in Q3, driven by the Infrastructure subledger expansion.',
    page: 'Slide 12',
    date: 'Aug 20, 2023',
    borderColor: 'border-l-secondary',
    badgeBg: 'bg-secondary/10 text-secondary',
  },
]

/* ─── component ─── */

export default function ChatSessionPage() {
  const params = useParams()
  const sessionId = params.sessionId as string

  const session = placeholderChatSessions().find((s) => s.id === sessionId)
  const messages = placeholderChatMessages()
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const [contextTab, setContextTab] = useState<'metadata' | 'charts' | 'links'>('metadata')

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  if (!session) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="flex flex-col items-center gap-md text-center"
        >
          <Icon size="48px" className="text-outline">
            chat_bubble
          </Icon>
          <h1 className="font-headline-md text-on-surface">Chat session not found</h1>
          <p className="font-body-md text-on-surface-variant">
            No session found with ID: {sessionId}
          </p>
          <Link
            href="/chat"
            className="mt-sm rounded bg-primary px-lg py-sm font-body-md font-bold text-on-primary transition-opacity hover:opacity-90"
          >
            Back to Chat
          </Link>
        </motion.div>
      </div>
    )
  }

  return (
    <div className="flex h-screen overflow-hidden bg-background text-on-surface">
      {/* ─── Left Sidebar — 260px ─── */}
      <motion.aside
        variants={sidebarVariants}
        initial="hidden"
        animate="show"
        className="fixed left-0 top-0 z-50 flex h-full w-[260px] flex-col border-r border-outline-variant bg-surface-container-lowest"
      >
        {/* Logo */}
        <div className="flex items-center gap-sm p-md pb-lg">
          <div className="flex h-8 w-8 items-center justify-center rounded bg-primary">
            <Icon fill className="text-on-primary" size="20px">
              lens
            </Icon>
          </div>
          <div>
            <h1 className="font-display text-headline-md font-bold leading-none text-primary">
              ProjectLens
            </h1>
            <p className="mt-1 font-label-md text-[10px] uppercase tracking-widest text-outline">
              Precision Intelligence
            </p>
          </div>
        </div>

        {/* New Analysis */}
        <div className="px-md pb-md">
          <button className="flex w-full items-center justify-center gap-sm rounded bg-primary-container py-sm font-body-md font-bold text-on-primary-container transition-opacity hover:opacity-90">
            <Icon size="18px">add</Icon>
            New Analysis
          </button>
        </div>

        {/* Chat History */}
        <nav className="flex-1 overflow-y-auto px-md custom-scrollbar">
          {/* Today */}
          <p className="mb-xs font-label-md text-on-surface-variant">Today</p>
          <div className="mb-md space-y-[2px]">
            {todayChats.map((chat) => (
              <Link
                key={chat.id}
                href={`/chat/${chat.id}`}
                className={`flex items-center gap-sm rounded px-sm py-sm transition-colors ${
                  chat.active
                    ? 'border-r-2 border-primary bg-primary-container/10 font-bold text-primary'
                    : 'text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface'
                }`}
              >
                <Icon size="18px" fill={chat.active}>
                  chat_bubble
                </Icon>
                <span className="truncate font-body-md">{chat.title}</span>
              </Link>
            ))}
          </div>

          {/* Yesterday */}
          <p className="mb-xs font-label-md text-on-surface-variant">Yesterday</p>
          <div className="space-y-[2px]">
            {yesterdayChats.map((chat) => (
              <Link
                key={chat.id}
                href={`/chat/${chat.id}`}
                className={`flex items-center gap-sm rounded px-sm py-sm transition-colors ${
                  chat.active
                    ? 'border-r-2 border-primary bg-primary-container/10 font-bold text-primary'
                    : 'text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface'
                }`}
              >
                <Icon size="18px" fill={chat.active}>
                  chat_bubble
                </Icon>
                <span className="truncate font-body-md">{chat.title}</span>
              </Link>
            ))}
          </div>
        </nav>

        {/* Bottom section */}
        <div className="mt-auto border-t border-outline-variant px-md py-sm">
          <Link
            href="#"
            className="flex items-center gap-md rounded p-sm text-on-surface-variant transition-colors hover:bg-surface-container-high hover:text-on-surface"
          >
            <Icon size="20px">help</Icon>
            <span className="font-body-md">Support</span>
          </Link>
          <Link
            href="#"
            className="flex items-center gap-md rounded p-sm text-on-surface-variant transition-colors hover:bg-surface-container-high hover:text-on-surface"
          >
            <Icon size="20px">code</Icon>
            <span className="font-body-md">API Keys</span>
          </Link>

          <div className="mt-sm flex items-center gap-sm rounded p-sm">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center overflow-hidden rounded-full border border-outline-variant bg-surface-variant">
              <Icon size="18px" className="text-on-surface-variant">
                person
              </Icon>
            </div>
            <div className="flex flex-1 flex-col">
              <span className="font-body-md text-xs font-bold text-on-surface">Alex Rivera</span>
              <span className="font-label-md text-[10px] text-on-surface-variant">Pro Plan</span>
            </div>
            <button className="text-outline transition-colors hover:text-on-surface">
              <Icon size="18px">settings</Icon>
            </button>
          </div>
        </div>
      </motion.aside>

      {/* ─── Main Chat Area ─── */}
      <main className="ml-[260px] mr-[320px] flex flex-1 flex-col h-screen">
        {/* Top Navbar */}
        <motion.header
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.35, delay: 0.1 }}
          className="sticky top-0 z-40 flex h-16 items-center justify-between border-b border-outline-variant bg-surface/80 px-xl backdrop-blur-xl"
        >
          <div className="flex items-center gap-md">
            {/* Save indicator */}
            <div className="glass-card-hover flex items-center gap-sm rounded px-sm py-1">
              <Icon size="16px" className="text-outline">
                history
              </Icon>
              <span className="font-label-md text-on-surface-variant">Saved 2m ago</span>
            </div>

            <div className="h-4 w-px bg-outline-variant" />

            <nav className="flex items-center gap-lg">
              <a
                href="#"
                className="font-body-md text-on-surface-variant transition-colors hover:text-on-surface"
              >
                Docs
              </a>
              <a
                href="#"
                className="font-body-md text-on-surface-variant transition-colors hover:text-on-surface"
              >
                Community
              </a>
            </nav>
          </div>

          <div className="flex items-center gap-md">
            <button className="text-on-surface-variant transition-colors hover:text-on-surface">
              <Icon>notifications</Icon>
            </button>
            <button className="text-on-surface-variant transition-colors hover:text-on-surface">
              <Icon>dark_mode</Icon>
            </button>
            <button className="flex items-center gap-sm rounded bg-primary px-md py-1.5 font-body-md font-bold text-on-primary transition-opacity hover:opacity-90">
              <Icon size="18px">share</Icon>
              Share
            </button>
            <div className="flex h-8 w-8 items-center justify-center overflow-hidden rounded-full border border-outline-variant bg-surface-container-high">
              <Icon size="18px" className="text-on-surface-variant">
                person
              </Icon>
            </div>
          </div>
        </motion.header>

        {/* Message Stream */}
        <div className="custom-scrollbar flex-1 overflow-y-auto px-xl py-lg">
          <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="show"
            className="mx-auto max-w-4xl space-y-xl"
          >
            {/* --- User Message --- */}
            <motion.div variants={messageVariants} className="flex gap-lg">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded bg-surface-variant">
                <Icon size="18px" className="text-on-surface-variant">
                  person
                </Icon>
              </div>
              <div className="min-w-0 flex-1">
                <p className="font-body-md leading-relaxed text-on-surface">
                  Compare the revenue growth of{' '}
                  <span className="rounded bg-primary/20 px-1 text-primary">
                    @Q3_Earnings_Report
                  </span>{' '}
                  versus{' '}
                  <span className="rounded bg-primary/20 px-1 text-primary">
                    @Q2_Strategic_Review
                  </span>
                  . Highlight any anomalies in the operational expenses.
                </p>
              </div>
            </motion.div>

            {/* --- AI Response --- */}
            <motion.div variants={messageVariants} className="flex gap-lg">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded bg-primary shadow-[0_0_12px_rgba(192,193,255,0.15)]">
                <Icon fill className="text-on-primary" size="18px">
                  smart_toy
                </Icon>
              </div>
              <div className="min-w-0 flex-1 space-y-md">
                {/* Intro paragraph */}
                <p className="font-body-md leading-relaxed text-on-surface">
                  Based on the analyzed documents, revenue grew at a{' '}
                  <span className="font-bold text-secondary">14.2% acceleration</span> in Q3
                  compared to Q2, driven primarily by the Infrastructure expansion initiative.
                  However, operational expenses reveal several notable anomalies worth
                  investigating.
                </p>

                {/* Key Findings card */}
                <div className="ai-gradient-border rounded-xl p-md">
                  <div className="flex items-center gap-sm">
                    <Icon size="18px" className="text-primary">
                      analytics
                    </Icon>
                    <span className="font-body-md font-bold text-primary">Key Findings</span>
                  </div>
                  <ul className="mt-sm space-y-sm">
                    <li className="flex items-start gap-sm font-body-md text-on-surface">
                      <span className="mt-[5px] h-2 w-2 shrink-0 rounded-full bg-primary" />
                      Infrastructure subledger shows a{' '}
                      <span className="font-bold text-primary">23% overspend</span> compared to
                      the same period last year
                    </li>
                    <li className="flex items-start gap-sm font-body-md text-on-surface">
                      <span className="mt-[5px] h-2 w-2 shrink-0 rounded-full bg-primary" />
                      Marketing cost per acquisition spiked{' '}
                      <span className="font-bold text-primary">18% QoQ</span> without
                      corresponding revenue impact
                    </li>
                  </ul>
                </div>

                {/* Follow-up paragraph */}
                <p className="font-body-md leading-relaxed text-on-surface">
                  These findings suggest that while the top-line growth is strong, the{' '}
                  <span className="rounded bg-primary/20 px-1 text-primary">
                    @Infrastructure_Subledger
                  </span>{' '}
                  requires immediate attention. The overspend pattern correlates with the cloud
                  migration timeline initiated in Q2.
                </p>

                {/* Streaming cursor */}
                <span className="inline-block h-[1em] w-[2px] animate-pulse bg-primary align-text-bottom" />

                {/* Citation chips */}
                <div className="flex flex-wrap gap-sm pt-sm">
                  <span className="inline-flex items-center gap-xs rounded-full border border-outline-variant bg-surface-container-high px-sm py-1 font-label-md text-on-surface-variant">
                    <Icon size="14px">description</Icon>
                    Q3_Earnings.pdf p.24
                  </span>
                  <span className="inline-flex items-center gap-xs rounded-full border border-outline-variant bg-surface-container-high px-sm py-1 font-label-md text-on-surface-variant">
                    <Icon size="14px">description</Icon>
                    Q2_Review.xlsx Row 142
                  </span>
                </div>
              </div>
            </motion.div>

            <div ref={messagesEndRef} />
          </motion.div>
        </div>

        {/* Input Bar */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.3 }}
          className="relative px-xl pb-lg"
        >
          {/* Gradient overlay */}
          <div className="pointer-events-none absolute -top-12 left-0 right-0 h-12 bg-gradient-to-t from-background to-transparent" />

          <div className="ai-gradient-border rounded-xl">
            <div className="rounded-xl bg-surface-container-low p-md">
              {/* Badge + chips row */}
              <div className="mb-sm flex flex-wrap items-center gap-sm">
                <span className="rounded bg-secondary-container/20 px-sm py-0.5 font-label-md text-secondary">
                  COMPARE MODE
                </span>
                <span className="inline-flex items-center gap-xs rounded bg-primary-container/20 px-sm py-0.5 font-label-md text-primary">
                  @Q3_Earnings
                  <button className="text-primary/60 transition-colors hover:text-primary">
                    <Icon size="14px">close</Icon>
                  </button>
                </span>
                <span className="inline-flex items-center gap-xs rounded bg-primary-container/20 px-sm py-0.5 font-label-md text-primary">
                  @Q2_Review
                  <button className="text-primary/60 transition-colors hover:text-primary">
                    <Icon size="14px">close</Icon>
                  </button>
                </span>
              </div>

              {/* Textarea + actions */}
              <div className="flex items-end gap-sm">
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ask ProjectLens AI... use @ to mention reports"
                  rows={2}
                  className="max-h-32 min-h-[44px] flex-1 resize-none border-0 bg-transparent px-sm py-1.5 font-body-md text-on-surface placeholder-outline outline-none"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault()
                    }
                  }}
                />
                <div className="flex items-center gap-xs">
                  <button className="flex h-8 w-8 items-center justify-center rounded text-outline transition-colors hover:text-on-surface">
                    <Icon size="20px">attach_file</Icon>
                  </button>
                  <button className="flex h-8 w-8 items-center justify-center rounded text-outline transition-colors hover:text-on-surface">
                    <Icon size="20px">mic</Icon>
                  </button>
                  <button className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-on-primary transition-opacity hover:opacity-90">
                    <Icon size="18px">arrow_upward</Icon>
                  </button>
                </div>
              </div>

              {/* Bottom hint */}
              <div className="mt-sm flex items-center justify-between px-sm">
                <span className="font-label-md text-outline">
                  ProjectLens AI can make mistakes. Verify important info.
                </span>
                <span className="font-label-md text-outline">1.2k tokens used</span>
              </div>
            </div>
          </div>
        </motion.div>
      </main>

      {/* ─── Right Context Panel — 320px ─── */}
      <motion.aside
        variants={contextPanelVariants}
        initial="hidden"
        animate="show"
        className="fixed right-0 top-0 z-50 flex h-full w-[320px] flex-col border-l border-outline-variant bg-surface-container-lowest"
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-outline-variant px-md py-md">
          <h2 className="font-headline-md text-on-surface">Source Context</h2>
          <button className="text-outline transition-colors hover:text-on-surface">
            <Icon size="20px">close</Icon>
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-outline-variant px-md">
          {(['metadata', 'charts', 'links'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setContextTab(tab)}
              className={`px-md py-sm font-body-md capitalize transition-colors ${
                contextTab === tab
                  ? 'border-b-2 border-primary font-bold text-primary'
                  : 'text-on-surface-variant hover:text-on-surface'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="custom-scrollbar flex-1 overflow-y-auto p-md space-y-md">
          {/* Source Card 1 */}
          <SourceCard
            source={contextSources[0]!}
            labelClass="text-primary"
            badgeClass="text-primary"
            transitionDelay={0.2}
          />

          {/* Source Card 2 */}
          <SourceCard
            source={contextSources[1]!}
            labelClass="text-secondary"
            badgeClass="text-secondary"
            transitionDelay={0.3}
          />

          {/* Image Preview */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.35 }}
            className="group relative h-40 overflow-hidden rounded-xl border border-outline-variant bg-surface-container-high"
          >
            <div className="flex h-full items-center justify-center">
              <Icon size="48px" className="text-outline">image</Icon>
            </div>
            <div className="absolute inset-0 flex items-center justify-center bg-black/50 opacity-0 transition-opacity group-hover:opacity-100">
              <div className="flex items-center gap-sm rounded bg-surface-container-low px-md py-sm">
                <Icon size="18px" className="text-on-surface">
                  zoom_in
                </Icon>
                <span className="font-body-md text-on-surface">Preview</span>
              </div>
            </div>
          </motion.div>

          {/* Bottom actions */}
          <div className="space-y-sm pt-sm">
            <button className="flex w-full items-center justify-center gap-sm rounded-lg border border-outline-variant bg-surface-container-low px-md py-sm font-body-md text-on-surface transition-colors hover:bg-surface-container-high">
              <Icon size="18px">folder_zip</Icon>
              Export All Sources (ZIP)
            </button>
            <button className="flex w-full items-center justify-center gap-sm rounded-lg border border-outline-variant bg-surface-container-low px-md py-sm font-body-md text-on-surface transition-colors hover:bg-surface-container-high">
              <Icon size="18px">verified_user</Icon>
              Audit AI Logic
            </button>
          </div>
        </div>
      </motion.aside>
    </div>
  )
}
