'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { DashboardLayout } from '@/components/layout/dashboard-layout'
import { Icon } from '@/components/shared/icon'
import { CollectionService } from '@/services/collections'
import type { Collection } from '@/types'

/* ─── animation helpers ─── */

const containerVariants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.06 } },
}

const itemVariants = {
  hidden: { opacity: 0, y: 24 },
  show: { opacity: 1, y: 0, transition: { duration: 0.45, ease: 'easeOut' as const } },
}

/* ─── helpers ─── */

function timeAgo(dateStr: string): string {
  const date = new Date(dateStr)
  if (Number.isNaN(date.getTime())) return ''
  const sec = Math.floor((Date.now() - date.getTime()) / 1000)
  if (sec < 60) return 'Just now'
  const min = Math.floor(sec / 60)
  if (min < 60) return `${min}m ago`
  const hr = Math.floor(min / 60)
  if (hr < 24) return `${hr}h ago`
  const d = Math.floor(hr / 24)
  if (d < 30) return `${d}d ago`
  const mo = Math.floor(d / 30)
  return mo < 12 ? `${mo}mo ago` : `${Math.floor(mo / 12)}y ago`
}

/* ─── Collection Card ─── */

function CollectionCard({ collection, index }: { collection: Collection; index: number }) {
  const themes = [
    'bg-primary/10 border-primary/20 text-primary',
    'bg-secondary/10 border-secondary/20 text-secondary',
    'bg-tertiary/10 border-tertiary/20 text-tertiary',
    'bg-primary/10 border-primary/20 text-primary',
  ]
  const t = themes[index % themes.length]

  return (
    <motion.div variants={itemVariants}>
      <a
        href={`/collections/${collection.id}`}
        className="glass-card group flex flex-col rounded-xl border border-outline-variant p-lg transition-all duration-300 hover:-translate-y-0.5 hover:border-[rgba(192,193,255,0.4)] hover:bg-[rgba(14,14,16,0.9)]"
      >
        {/* Top row */}
        <div className="mb-lg flex items-start justify-between">
          <div
            className={`flex h-12 w-12 items-center justify-center rounded-lg border ${t}`}
          >
            <Icon size="22px">folder</Icon>
          </div>
          <span className="rounded-full bg-surface-container-high px-sm py-0.5 font-label-md text-on-surface-variant">
            {collection.reportCount} {collection.reportCount === 1 ? 'report' : 'reports'}
          </span>
        </div>

        {/* Body */}
        <div className="flex-1">
          <h3 className="mb-xs font-headline-md text-on-surface group-hover:text-primary transition-colors">
            {collection.name}
          </h3>
          <p className="line-clamp-2 font-body-md text-on-surface-variant">
            {collection.description || 'No description provided.'}
          </p>
        </div>

        {/* Footer */}
        <div className="mt-xl flex items-center justify-between border-t border-outline-variant pt-md">
          <span className="font-label-md text-outline">
            {collection.updatedAt ? `Updated ${timeAgo(collection.updatedAt)}` : ''}
          </span>
          <Icon size="16px" className="text-outline opacity-0 transition-opacity group-hover:opacity-100">
            arrow_right_alt
          </Icon>
        </div>
      </a>
    </motion.div>
  )
}

/* ─── Create Collection Button ─── */

function CreateCollectionButton() {
  const router = useRouter()
  const [creating, setCreating] = useState(false)
  const [name, setName] = useState('')
  const [open, setOpen] = useState(false)

  const create = async () => {
    const trimmed = name.trim()
    if (!trimmed || creating) return
    setCreating(true)
    try {
      const c = await CollectionService.create({ name: trimmed })
      router.push(`/collections/${c.id}`)
    } catch {
      setCreating(false)
    }
  }

  return (
    <motion.div variants={itemVariants}>
      {open ? (
        <div className="glass-card flex h-full min-h-[220px] flex-col gap-md rounded-xl border border-primary/30 p-lg">
          <p className="font-headline-md text-on-surface">Name your collection</p>
          <input
            autoFocus
            value={name}
            onChange={(e) => setName(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') create() }}
            placeholder="e.g. Q4 Financial Reports"
            className="w-full rounded-lg border border-outline-variant bg-surface-container-lowest px-md py-sm font-body-md text-on-surface outline-none placeholder:text-outline focus:border-primary focus:ring-1 focus:ring-primary/50"
          />
          <div className="mt-auto flex gap-sm">
            <button
              onClick={create}
              disabled={creating || !name.trim()}
              className="flex-1 rounded-lg bg-primary py-sm font-body-md font-bold text-on-primary transition-opacity hover:opacity-90 disabled:opacity-40"
            >
              {creating ? 'Creating…' : 'Create'}
            </button>
            <button
              onClick={() => setOpen(false)}
              className="rounded-lg border border-outline-variant px-md py-sm font-body-md text-on-surface-variant transition-colors hover:bg-surface-container-high"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <button
          onClick={() => setOpen(true)}
          className="flex h-full min-h-[220px] w-full flex-col items-center justify-center gap-md rounded-xl border-2 border-dashed border-outline-variant transition-all group hover:border-primary/50 hover:bg-surface-container-high"
        >
          <div className="flex h-12 w-12 items-center justify-center rounded-full border border-outline-variant transition-colors group-hover:border-primary group-hover:text-primary">
            <Icon size="24px">add</Icon>
          </div>
          <span className="font-bold text-on-surface-variant transition-colors group-hover:text-on-surface">
            Create Collection
          </span>
        </button>
      )}
    </motion.div>
  )
}

/* ─── Page Component ─── */

export default function CollectionsPage() {
  const [collections, setCollections] = useState<Collection[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        const data = await CollectionService.list({ limit: 100 })
        if (!cancelled) setCollections(data)
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Failed to load collections')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [])

  return (
    <DashboardLayout>
      <div className="custom-scrollbar relative p-xl">
        {/* Background glow */}
        <div className="pointer-events-none absolute right-0 top-0 -z-10 h-[600px] w-[600px] rounded-full bg-primary/5 blur-[120px]" />

        {/* ─── Page Header ─── */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, ease: 'easeOut' }}
          className="mb-xl flex items-end justify-between"
        >
          <div>
            <h1 className="font-headline-lg text-on-surface">Collections</h1>
            <p className="mt-sm max-w-xl font-body-md text-on-surface-variant">
              Organize your analysis reports into thematic collections for faster retrieval
              and cross-reference insights.
            </p>
          </div>
        </motion.div>

        {/* ─── Loading ─── */}
        {loading && (
          <div className="grid grid-cols-1 gap-lg md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="glass-card min-h-[220px] animate-pulse rounded-xl border border-outline-variant p-lg">
                <div className="mb-lg h-12 w-12 rounded-lg bg-surface-container-high" />
                <div className="h-5 w-3/4 rounded bg-surface-container-high" />
                <div className="mt-md h-4 w-full rounded bg-surface-container-high" />
                <div className="mt-sm h-4 w-2/3 rounded bg-surface-container-high" />
              </div>
            ))}
          </div>
        )}

        {/* ─── Error ─── */}
        {error && !loading && (
          <div className="flex items-center justify-center py-32">
            <div className="glass-card max-w-md rounded-xl p-xl text-center">
              <Icon className="mb-md text-error" size="40px">error_outline</Icon>
              <h2 className="mb-sm font-headline-md text-on-surface">Failed to load collections</h2>
              <p className="mb-lg font-body-md text-on-surface-variant">{error}</p>
              <button
                onClick={() => window.location.reload()}
                className="rounded-lg bg-primary px-lg py-sm font-headline-md text-on-primary transition-colors hover:opacity-90"
              >
                Try Again
              </button>
            </div>
          </div>
        )}

        {/* ─── Grid ─── */}
        {!loading && !error && (
          <motion.div
            className="grid grid-cols-1 gap-lg md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
            variants={containerVariants}
            initial="hidden"
            animate="show"
          >
            {collections.map((c, i) => (
              <CollectionCard key={c.id} collection={c} index={i} />
            ))}

            {/* Create Collection Button */}
            <CreateCollectionButton />
          </motion.div>
        )}

        {/* ─── Empty State ─── */}
        {!loading && !error && collections.length === 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex flex-col items-center gap-md py-32 text-center"
          >
            <Icon size="48px" className="text-outline">folder_open</Icon>
            <h2 className="font-headline-md text-on-surface">No collections yet</h2>
            <p className="font-body-md text-on-surface-variant">
              Create your first collection to organize reports by theme or department.
            </p>
          </motion.div>
        )}
      </div>
    </DashboardLayout>
  )
}
