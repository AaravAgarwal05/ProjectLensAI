'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { DashboardLayout } from '@/components/layout/dashboard-layout'
import { Icon } from '@/components/shared/icon'
import { CollectionService } from '@/services/collections'
import { useToast } from '@/providers/toast-provider'
import type { Collection } from '@/types'

const reveal = {
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.4, ease: 'easeOut' as const },
}

export default function CollectionDetailPage({
  params,
}: {
  params: Promise<{ collectionId: string }>
}) {
  const router = useRouter()
  const { addToast, confirmToast } = useToast()
  const [collection, setCollection] = useState<Collection | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      const { collectionId } = await params
      try {
        const data = await CollectionService.getById(collectionId)
        if (!cancelled) setCollection(data)
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Failed to load collection')
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => { cancelled = true }
  }, [params])

  const handleDelete = () => {
    if (!collection) return
    confirmToast('Delete this collection permanently?', async () => {
      try {
        await CollectionService.delete(collection.id)
        addToast('Collection deleted', 'success')
        router.push('/collections')
      } catch {
        addToast('Could not delete collection. Try again.', 'error')
      }
    })
  }

  /* ─── Loading skeleton ─── */
  if (loading) {
    return (
      <DashboardLayout>
        <div className="p-xl">
          <div className="mb-lg">
            <div className="h-4 w-40 animate-pulse rounded bg-surface-container-high" />
            <div className="mt-md h-8 w-72 animate-pulse rounded bg-surface-container-high" />
            <div className="mt-sm h-4 w-96 max-w-full animate-pulse rounded bg-surface-container-high" />
          </div>
          <div className="grid gap-lg lg:grid-cols-3">
            <div className="h-64 animate-pulse rounded-xl bg-surface-container-high lg:col-span-2" />
            <div className="h-48 animate-pulse rounded-xl bg-surface-container-high" />
          </div>
        </div>
      </DashboardLayout>
    )
  }

  /* ─── Not found / error ─── */
  if (error || !collection) {
    return (
      <DashboardLayout>
        <div className="flex h-full items-center justify-center p-xl">
          <motion.div
            initial={{ opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            className="glass-card max-w-md rounded-xl p-xl text-center"
          >
            <Icon size="44px" className="mx-auto mb-md text-outline">folder_open</Icon>
            <h1 className="font-headline-md text-on-surface">Collection not found</h1>
            <p className="mt-sm font-body-md text-on-surface-variant">
              {error || 'No collection found with this ID.'}
            </p>
            <Link
              href="/collections"
              className="mt-lg inline-block rounded-lg bg-primary px-lg py-sm font-body-md font-bold text-on-primary transition-opacity hover:opacity-90"
            >
              Back to Collections
            </Link>
          </motion.div>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <div className="custom-scrollbar p-xl">
        {/* ─── Header ─── */}
        <motion.div {...reveal} className="mb-xl">
          <div className="mb-sm flex items-center gap-sm font-label-md text-on-surface-variant">
            <Link href="/collections" className="transition-colors hover:text-on-surface">
              Collections
            </Link>
            <Icon size="14px">chevron_right</Icon>
            <span className="text-on-surface">{collection.name}</span>
          </div>
          <div className="flex flex-wrap items-start justify-between gap-md">
            <div className="min-w-0">
              <h1 className="font-headline-lg text-on-surface">{collection.name}</h1>
              <p className="mt-sm font-body-md text-on-surface-variant">
                {collection.description || 'No description provided.'}
              </p>
            </div>
            <button
              onClick={handleDelete}
              className="flex shrink-0 items-center gap-sm rounded-lg border border-error/30 px-lg py-sm font-body-md font-bold text-error transition-colors hover:bg-error/10"
            >
              <Icon size="18px">delete</Icon>
              Delete Collection
            </button>
          </div>
        </motion.div>

        <div className="grid gap-lg lg:grid-cols-3">
          {/* ─── Main ─── */}
          <motion.div {...reveal} className="lg:col-span-2">
            <div className="glass-card rounded-xl p-lg">
              <h2 className="mb-sm font-headline-md text-on-surface">Reports</h2>
              <p className="mb-lg font-body-md text-on-surface-variant">
                {collection.reportCount} {collection.reportCount === 1 ? 'report' : 'reports'} in collection
              </p>
              {collection.reportCount === 0 ? (
                <div className="flex flex-col items-center gap-md py-16 text-center">
                  <Icon size="40px" className="text-outline">folder_open</Icon>
                  <p className="font-headline-md text-on-surface-variant">No reports yet</p>
                  <p className="font-body-md text-on-surface-variant">
                    Add reports from the Reports page to group them in this collection.
                  </p>
                  <Link
                    href="/reports"
                    className="mt-sm rounded-lg bg-primary px-lg py-sm font-body-md font-bold text-on-primary transition-opacity hover:opacity-90"
                  >
                    Browse Reports
                  </Link>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-md py-16 text-center">
                  <Icon size="40px" className="text-primary">description</Icon>
                  <p className="font-headline-md text-on-surface">
                    {collection.reportCount} {collection.reportCount === 1 ? 'report' : 'reports'}
                  </p>
                  <p className="font-body-md text-on-surface-variant">
                    Manage report membership from the Reports page.
                  </p>
                  <Link
                    href="/reports"
                    className="mt-sm rounded-lg bg-primary px-lg py-sm font-body-md font-bold text-on-primary transition-opacity hover:opacity-90"
                  >
                    Open Reports
                  </Link>
                </div>
              )}
            </div>
          </motion.div>

          {/* ─── Sidebar ─── */}
          <motion.div {...reveal} className="space-y-lg">
            <div className="glass-card rounded-xl p-lg">
              <h2 className="mb-lg font-headline-md text-on-surface">Collection Info</h2>
              <div className="space-y-md">
                {[
                  { label: 'Created', value: collection.createdAt ? collection.createdAt.slice(0, 10) : '—' },
                  { label: 'Updated', value: collection.updatedAt ? collection.updatedAt.slice(0, 10) : '—' },
                  { label: 'Reports', value: String(collection.reportCount) },
                ].map((row) => (
                  <div key={row.label} className="flex items-center justify-between">
                    <span className="font-label-md text-on-surface-variant">{row.label}</span>
                    <span className="font-body-md font-bold text-on-surface">{row.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </DashboardLayout>
  )
}
