'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { Icon } from '@/components/shared/icon'
import { ChatService } from '@/services/chat'
import type { ChatSession, ChatMessage } from '@/types/chat'

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
  citation,
  index,
}: {
  citation: { chunkId: string; sourceId: string; sourceTitle: string; score: number; text: string }
  index: number
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.1 * index }}
      className="glass-card rounded-xl p-md"
    >
      <div className="mb-sm flex items-center justify-between">
        <span className="font-label-md uppercase text-primary">Source {index + 1}</span>
        <span className="rounded-full bg-primary/10 px-sm py-0.5 font-label-md text-primary">
          {Math.round(citation.score * 100)}% match
        </span>
      </div>
      <p className="mt-xs line-clamp-3 font-body-md text-on-surface-variant">
        {citation.text || citation.sourceTitle || `Chunk: ${citation.chunkId.slice(0, 12)}...`}
      </p>
    </motion.div>
  )
}

/* ─── component ─── */

export default function ChatSessionPage() {
  const params = useParams()
  const sessionId = params.sessionId as string

  const [session, setSession] = useState<ChatSession | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [sessionsList, setSessionsList] = useState<ChatSession[]>([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Load session + messages + session list
  useEffect(() => {
    let cancelled = false
    async function load() {
      setLoading(true)
      setError('')
      try {
        const [s, msgs, all] = await Promise.all([
          ChatService.getSession(sessionId),
          ChatService.getMessages(sessionId),
          ChatService.listSessions({ limit: 50 }),
        ])
        if (cancelled) return
        setSession(s)
        setMessages(msgs)
        setSessionsList(all)
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Failed to load chat')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [sessionId])

  // Auto-scroll on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = useCallback(async () => {
    const text = input.trim()
    if (!text || sending) return
    setSending(true)

    // Optimistic user message
    const optimisticId = `temp-${Date.now()}`
    setMessages((prev) => [
      ...prev,
      { id: optimisticId, sessionId, role: 'user', content: text, createdAt: new Date().toISOString() },
    ])
    setInput('')

    // Add streaming assistant message placeholder
    const streamMsgId = `stream-${Date.now()}`
    setMessages((prev) => [
      ...prev,
      { id: streamMsgId, sessionId, role: 'assistant', content: '', createdAt: new Date().toISOString() },
    ])

    try {
      await ChatService.streamMessage(
        sessionId,
        text,
        (chunk) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === streamMsgId ? { ...m, content: m.content + chunk } : m
            )
          )
        },
        { reportIds: session?.reportIds, mode: session?.mode }
      )
    } catch {
      setMessages((prev) => prev.filter((m) => m.id !== streamMsgId || m.content))
      setError('Failed to send message. Try again.')
    } finally {
      setSending(false)
    }
  }, [input, sending, sessionId, session])

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }, [handleSend])

  // Last assistant message citations for right panel
  const lastAssistantMsg = [...messages].reverse().find((m) => m.role === 'assistant')

  /* ─── Loading ─── */
  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-md">
          <span className="inline-block h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          <p className="font-body-md text-on-surface-variant">Loading chat…</p>
        </div>
      </div>
    )
  }

  /* ─── Not Found / Error ─── */
  if (error || !session) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="flex flex-col items-center gap-md text-center"
        >
          <Icon size="48px" className="text-outline">chat_bubble</Icon>
          <h1 className="font-headline-md text-on-surface">
            {error ? 'Failed to load' : 'Chat session not found'}
          </h1>
          <p className="font-body-md text-on-surface-variant">
            {error || `No session found with ID: ${sessionId}`}
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

  const reportTitle = session.reportIds.length > 0
    ? `Report ${session.reportIds[0]!.slice(0, 8)}...`
    : null

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
            <Icon fill className="text-on-primary" size="20px">lens</Icon>
          </div>
          <div>
            <h1 className="font-display text-headline-md font-bold leading-none text-primary">ProjectLens</h1>
            <p className="mt-1 font-label-md text-[10px] uppercase tracking-widest text-outline">Precision Intelligence</p>
          </div>
        </div>

        {/* New Chat */}
        <div className="px-md pb-md">
          <Link
            href="/chat"
            className="flex w-full items-center justify-center gap-sm rounded bg-primary-container py-sm font-body-md font-bold text-on-primary-container transition-opacity hover:opacity-90"
          >
            <Icon size="18px">add</Icon>
            New Chat
          </Link>
        </div>

        {/* Chat History */}
        <nav className="flex-1 overflow-y-auto px-md custom-scrollbar">
          {sessionsList.length === 0 && (
            <p className="font-label-md text-outline text-center py-lg">No conversations yet</p>
          )}
          <div className="space-y-[2px]">
            {sessionsList.map((s) => (
              <Link
                key={s.id}
                href={`/chat/${s.id}`}
                className={`flex items-center gap-sm rounded px-sm py-sm transition-colors ${
                  s.id === sessionId
                    ? 'border-r-2 border-primary bg-primary-container/10 font-bold text-primary'
                    : 'text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface'
                }`}
              >
                <Icon size="18px" fill={s.id === sessionId}>chat_bubble</Icon>
                <span className="truncate font-body-md">{s.title}</span>
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
            <span className="font-headline-md text-on-surface truncate max-w-md">{session.title}</span>
            {reportTitle && (
              <>
                <span className="h-4 w-px bg-outline-variant" />
                <span className="font-label-md text-on-surface-variant">{reportTitle}</span>
              </>
            )}
          </div>

          <div className="flex items-center gap-md">
            <button className="text-on-surface-variant transition-colors hover:text-on-surface">
              <Icon>notifications</Icon>
            </button>
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
            {messages.length === 0 && (
              <motion.div variants={messageVariants} className="flex flex-col items-center py-24 text-center">
                <Icon size="48px" className="text-outline mb-md">smart_toy</Icon>
                <p className="font-headline-md text-on-surface mb-sm">Ask about this document</p>
                <p className="font-body-md text-on-surface-variant max-w-md">
                  Ask questions about the uploaded document and get AI-powered answers with citations.
                </p>
              </motion.div>
            )}

            {messages.map((msg) => (
              <motion.div key={msg.id} variants={messageVariants} className="flex gap-lg">
                <div
                  className={`flex h-8 w-8 shrink-0 items-center justify-center rounded ${
                    msg.role === 'user'
                      ? 'bg-surface-variant'
                      : 'bg-primary shadow-[0_0_12px_rgba(192,193,255,0.15)]'
                  }`}
                >
                  <Icon
                    size="18px"
                    className={msg.role === 'user' ? 'text-on-surface-variant' : 'text-on-primary'}
                    fill={msg.role === 'assistant'}
                  >
                    {msg.role === 'user' ? 'person' : 'smart_toy'}
                  </Icon>
                </div>
                <div className="min-w-0 flex-1">
                  <p className="font-body-md leading-relaxed text-on-surface whitespace-pre-wrap">
                    {msg.content}
                  </p>

                  {/* Citation chips */}
                  {msg.role === 'assistant' && msg.citations && msg.citations.length > 0 && (
                    <div className="mt-sm flex flex-wrap gap-sm">
                      {msg.citations.map((cit, i) => (
                        <span
                          key={`${cit.chunkId}-${i}`}
                          className="inline-flex items-center gap-xs rounded-full border border-outline-variant bg-surface-container-high px-sm py-1 font-label-md text-on-surface-variant"
                        >
                          <Icon size="14px">description</Icon>
                          Source {i + 1} · {Math.round(cit.score * 100)}%
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </motion.div>
            ))}

            {/* Typing indicator */}
            {sending && (
              <motion.div variants={messageVariants} className="flex gap-lg">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded bg-primary shadow-[0_0_12px_rgba(192,193,255,0.15)]">
                  <Icon fill className="text-on-primary" size="18px">smart_toy</Icon>
                </div>
                <div className="flex items-center gap-1">
                  <span className="inline-block h-2 w-2 animate-bounce rounded-full bg-outline" style={{ animationDelay: '0ms' }} />
                  <span className="inline-block h-2 w-2 animate-bounce rounded-full bg-outline" style={{ animationDelay: '150ms' }} />
                  <span className="inline-block h-2 w-2 animate-bounce rounded-full bg-outline" style={{ animationDelay: '300ms' }} />
                </div>
              </motion.div>
            )}

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
          <div className="pointer-events-none absolute -top-12 left-0 right-0 h-12 bg-gradient-to-t from-background to-transparent" />

          <div className="ai-gradient-border rounded-xl">
            <div className="rounded-xl bg-surface-container-low p-md">
              {/* Report badges */}
              {session.reportIds.length > 0 && (
                <div className="mb-sm flex flex-wrap items-center gap-sm">
                  {session.reportIds.map((rid) => (
                    <span
                      key={rid}
                      className="inline-flex items-center gap-xs rounded bg-primary-container/20 px-sm py-0.5 font-label-md text-primary"
                    >
                      <Icon size="14px">description</Icon>
                      Report {rid.slice(0, 8)}...
                    </span>
                  ))}
                </div>
              )}

              <div className="flex items-end gap-sm">
                <input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={
                    session.reportIds.length > 0
                      ? 'Ask about this document...'
                      : 'Ask ProjectLens AI...'
                  }
                  disabled={sending}
                  className="max-h-32 min-h-[44px] flex-1 resize-none border-0 bg-transparent px-sm py-1.5 font-body-md text-on-surface placeholder-outline outline-none"
                />
                <div className="flex items-center gap-xs">
                  <button
                    onClick={handleSend}
                    disabled={!input.trim() || sending}
                    className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-on-primary transition-opacity hover:opacity-90 disabled:opacity-30 disabled:cursor-not-allowed"
                  >
                    <Icon size="18px">arrow_upward</Icon>
                  </button>
                </div>
              </div>

              <div className="mt-sm flex items-center justify-between px-sm">
                <span className="font-label-md text-outline">
                  ProjectLens AI can make mistakes. Verify important info.
                </span>
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
          <h2 className="font-headline-md text-on-surface">
            {session.reportIds.length > 0 ? 'Document Sources' : 'Session Info'}
          </h2>
        </div>

        {/* Content */}
        <div className="custom-scrollbar flex-1 overflow-y-auto p-md space-y-md">
          {/* Report info */}
          {session.reportIds.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              className="glass-card rounded-xl p-md"
            >
              <div className="mb-sm flex items-center gap-sm">
                <Icon size="18px" className="text-primary">description</Icon>
                <span className="font-label-md uppercase text-primary">Linked Documents</span>
              </div>
              <div className="space-y-sm">
                {session.reportIds.map((rid) => (
                  <div key={rid} className="flex items-center gap-sm font-body-md text-on-surface-variant">
                    <Icon size="14px">article</Icon>
                    <span className="truncate font-label-sm">{rid}</span>
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          {/* Citations from last assistant message */}
          {lastAssistantMsg?.citations && lastAssistantMsg.citations.length > 0 && (
            <>
              <div className="flex items-center gap-sm pt-sm">
                <Icon size="18px" className="text-primary">travel_explore</Icon>
                <span className="font-label-md uppercase text-primary">Cited Sources</span>
              </div>
              {lastAssistantMsg.citations.map((cit, i) => (
                <SourceCard key={`${cit.chunkId}-${i}`} citation={cit} index={i} />
              ))}
            </>
          )}

          {!lastAssistantMsg?.citations?.length && session.reportIds.length === 0 && (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <Icon size="36px" className="text-outline mb-sm">info</Icon>
              <p className="font-body-md text-on-surface-variant">
                Ask a question to see sources and context here.
              </p>
            </div>
          )}
        </div>
      </motion.aside>
    </div>
  )
}
