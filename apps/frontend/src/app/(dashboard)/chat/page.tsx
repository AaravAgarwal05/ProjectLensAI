'use client'

import { useState } from 'react'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { DashboardLayout } from '@/components/layout/dashboard-layout'
import { Icon } from '@/components/shared/icon'
import { placeholderChatSessions } from '@/lib/placeholders'

/* ─── animation variants ─── */

const containerVariants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.06 } },
}

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { duration: 0.45, ease: 'easeOut' as const } },
}

/* ─── helpers ─── */

function timeAgo(date: Date): string {
  const sec = Math.floor((Date.now() - date.getTime()) / 1000)
  if (sec < 60) return 'Just now'
  const min = Math.floor(sec / 60)
  if (min < 60) return `${min}m ago`
  const hr = Math.floor(min / 60)
  if (hr < 24) return `${hr}h ago`
  const d = Math.floor(hr / 24)
  return `${d}d ago`
}

export default function ChatHomePage() {
  const [search, setSearch] = useState('')
  const sessions = placeholderChatSessions()

  const filtered = search
    ? sessions.filter(
        (s) =>
          s.title.toLowerCase().includes(search.toLowerCase()) ||
          s.mode.toLowerCase().includes(search.toLowerCase()),
      )
    : sessions

  return (
    <DashboardLayout>
      <div className="custom-scrollbar flex h-full flex-col p-xl">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, ease: 'easeOut' }}
          className="mb-xl flex flex-wrap items-center justify-between gap-md"
        >
          <div>
            <h1 className="font-headline-lg text-on-surface">Chat Sessions</h1>
            <p className="mt-sm font-body-md text-on-surface-variant">
              Ask questions and analyze your documents
            </p>
          </div>

          <Link
            href="/chat/new"
            className="flex items-center gap-sm rounded bg-primary px-lg py-sm font-body-md font-bold text-on-primary transition-opacity hover:opacity-90"
          >
            <Icon size="18px">add</Icon>
            New Chat
          </Link>
        </motion.div>

        {/* Search */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.1, ease: 'easeOut' }}
          className="relative mb-xl max-w-md"
        >
          <Icon
            size="18px"
            className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-outline"
          >
            search
          </Icon>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search chat sessions..."
            className="w-full rounded-lg border border-outline-variant bg-surface-container-lowest py-2 pl-10 pr-md font-body-md text-on-surface outline-none placeholder:text-outline focus:ring-1 focus:ring-primary/50"
          />
        </motion.div>

        {/* Chat list */}
        {filtered.length === 0 ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="flex flex-1 flex-col items-center justify-center gap-md py-xxl text-center"
          >
            <Icon size="48px" className="text-outline">
              chat_bubble
            </Icon>
            <p className="font-headline-md text-on-surface-variant">No chat sessions yet</p>
            <p className="font-body-md text-outline">
              {search ? 'Try a different search term.' : 'Start a new chat to analyze your documents.'}
            </p>
          </motion.div>
        ) : (
          <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="show"
            className="grid gap-md sm:grid-cols-2 lg:grid-cols-3"
          >
            {filtered.map((session) => (
              <motion.div key={session.id} variants={itemVariants}>
                <Link
                  href={`/chat/${session.id}`}
                  className="group relative block rounded-xl border border-outline-variant bg-surface-container-low p-md transition-all hover:border-primary/30 hover:bg-surface-container-high"
                >
                  {/* Icon */}
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-container/20">
                    <Icon size="20px" className="text-primary">
                      chat_bubble
                    </Icon>
                  </div>

                  {/* Title */}
                  <h3 className="mt-md font-body-md font-bold text-on-surface group-hover:text-primary transition-colors">
                    {session.title}
                  </h3>

                  {/* Preview */}
                  <p className="mt-xs line-clamp-2 font-body-md text-on-surface-variant">
                    {session.mode === 'comparison'
                      ? 'Comparing reports across dimensions...'
                      : session.mode === 'multi'
                        ? 'Multi-report analysis session...'
                        : 'Single report analysis session...'}
                  </p>

                  {/* Footer */}
                  <div className="mt-md flex items-center justify-between border-t border-outline-variant/50 pt-sm">
                    <span className="font-label-md text-outline">
                      {session.messageCount} messages
                    </span>
                    <span className="font-label-md text-outline">
                      {session.createdAt ? timeAgo(new Date(session.createdAt)) : ''}
                    </span>
                  </div>

                  {/* Hover arrow */}
                  <Icon
                    size="16px"
                    className="absolute right-md top-md text-outline opacity-0 transition-opacity group-hover:opacity-100"
                  >
                    arrow_right_alt
                  </Icon>
                </Link>
              </motion.div>
            ))}
          </motion.div>
        )}
      </div>
    </DashboardLayout>
  )
}
