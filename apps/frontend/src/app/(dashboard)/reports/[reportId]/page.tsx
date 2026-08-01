'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { DashboardLayout } from '@/components/layout/dashboard-layout'
import { Icon } from '@/components/shared/icon'
import { ReportService } from '@/services/reports'
import { ChatService } from '@/services/chat'
import { useToast } from '@/providers/toast-provider'
import type { Report, ReportVersion } from '@/types'

function formatFileSize(bytes: number | undefined): string {
  if (!bytes) return '—'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`
}

const reveal = {
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.4, ease: 'easeOut' as const },
}

export default function ReportDetailPage({
  params,
}: {
  params: Promise<{ reportId: string }>
}) {
  const router = useRouter()
  const { addToast, confirmToast } = useToast()
  const [report, setReport] = useState<Report | null>(null)
  const [versions, setVersions] = useState<ReportVersion[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      const { reportId } = await params
      try {
        const [r, v] = await Promise.all([
          ReportService.getById(reportId),
          ReportService.getVersions(reportId),
        ])
        if (cancelled) return
        setReport(r)
        setVersions(v)
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Failed to load report')
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => { cancelled = true }
  }, [params])

  const handleDelete = () => {
    if (!report || deleting) return
    confirmToast('Delete this report permanently?', async () => {
      setDeleting(true)
      try {
        await ReportService.delete(report.id)
        addToast('Report deleted', 'success')
        router.push('/reports')
      } catch {
        addToast('Could not delete report. Try again.', 'error')
        setDeleting(false)
      }
    })
  }

  const handleOpenChat = async () => {
    if (!report) return
    try {
      const session = await ChatService.createSession({
        title: report.title,
        reportIds: [report.id],
        mode: 'single',
      })
      router.push(`/chat/${session.id}`)
    } catch {
      addToast('Failed to create chat session. Please try again.', 'error')
    }
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
            <div className="space-y-lg lg:col-span-2">
              <div className="h-72 animate-pulse rounded-xl bg-surface-container-high" />
              <div className="h-40 animate-pulse rounded-xl bg-surface-container-high" />
            </div>
            <div className="h-64 animate-pulse rounded-xl bg-surface-container-high" />
          </div>
        </div>
      </DashboardLayout>
    )
  }

  /* ─── Not found / error ─── */
  if (error || !report) {
    return (
      <DashboardLayout>
        <div className="flex h-full items-center justify-center p-xl">
          <motion.div
            initial={{ opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            className="glass-card max-w-md rounded-xl p-xl text-center"
          >
            <Icon size="44px" className="mx-auto mb-md text-outline">description</Icon>
            <h1 className="font-headline-md text-on-surface">Report not found</h1>
            <p className="mt-sm font-body-md text-on-surface-variant">
              {error || 'No report found with this ID.'}
            </p>
            <Link
              href="/reports"
              className="mt-lg inline-block rounded-lg bg-primary px-lg py-sm font-body-md font-bold text-on-primary transition-opacity hover:opacity-90"
            >
              Back to Reports
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
            <Link href="/reports" className="transition-colors hover:text-on-surface">
              Reports
            </Link>
            <Icon size="14px">chevron_right</Icon>
            <span className="text-on-surface">{report.title}</span>
          </div>
          <div className="flex flex-wrap items-start justify-between gap-md">
            <div className="min-w-0">
              <h1 className="font-headline-lg text-on-surface">{report.title}</h1>
              {report.description && (
                <p className="mt-sm font-body-md text-on-surface-variant">{report.description}</p>
              )}
            </div>
            <div className="flex shrink-0 gap-sm">
              <button
                onClick={handleOpenChat}
                className="flex items-center gap-sm rounded-lg bg-primary px-lg py-sm font-body-md font-bold text-on-primary transition-opacity hover:opacity-90"
              >
                <Icon size="18px">smart_toy</Icon>
                Open in Chat
              </button>
              <button
                onClick={handleDelete}
                disabled={deleting}
                className="flex items-center gap-sm rounded-lg border border-error/30 px-lg py-sm font-body-md font-bold text-error transition-colors hover:bg-error/10 disabled:opacity-50"
              >
                <Icon size="18px">delete</Icon>
                {deleting ? 'Deleting…' : 'Delete'}
              </button>
            </div>
          </div>
        </motion.div>

        <div className="grid gap-lg lg:grid-cols-3">
          {/* ─── Main ─── */}
          <div className="space-y-lg lg:col-span-2">
            {/* Metadata */}
            <motion.section {...reveal} className="glass-card rounded-xl p-lg">
              <h2 className="mb-lg font-headline-md text-on-surface">Metadata</h2>
              <div className="grid grid-cols-2 gap-lg sm:grid-cols-3">
                {[
                  { label: 'Author', value: report.author || '—' },
                  { label: 'Department', value: report.department || '—' },
                  { label: 'Status', value: report.status, status: true },
                  { label: 'Visibility', value: report.visibility },
                  { label: 'File size', value: formatFileSize(report.fileSize) },
                  { label: 'Type', value: report.mimeType || '—' },
                  { label: 'Created', value: report.createdAt.slice(0, 10) },
                  { label: 'Updated', value: report.updatedAt.slice(0, 10) },
                  { label: 'Year', value: report.year ? String(report.year) : '—' },
                ].map((f) => (
                  <div key={f.label}>
                    <p className="font-label-md text-[11px] uppercase tracking-wider text-on-surface-variant">
                      {f.label}
                    </p>
                    <p className={`mt-sm font-body-md font-bold text-on-surface ${f.status ? 'capitalize text-primary' : ''}`}>
                      {f.value}
                    </p>
                  </div>
                ))}
              </div>
              {report.tags && report.tags.length > 0 && (
                <div className="mt-lg flex flex-wrap gap-sm border-t border-outline-variant pt-lg">
                  {report.tags.map((tag) => (
                    <span
                      key={tag}
                      className="inline-flex items-center gap-xs rounded-full bg-primary-container/20 px-sm py-0.5 font-label-md text-primary"
                    >
                      <Icon size="14px">tag</Icon>
                      {tag}
                    </span>
                  ))}
                </div>
              )}
            </motion.section>

            {/* Versions */}
            <motion.section {...reveal} className="glass-card rounded-xl p-lg">
              <h2 className="mb-sm font-headline-md text-on-surface">Versions</h2>
              <p className="mb-lg font-body-md text-on-surface-variant">Version history for this report</p>
              {versions.length === 0 ? (
                <p className="font-body-md text-on-surface-variant">No versions recorded.</p>
              ) : (
                <div className="space-y-sm">
                  {versions.map((v, i) => (
                    <div
                      key={v.id}
                      className="flex items-center justify-between rounded-lg border border-outline-variant bg-surface-container-lowest p-md"
                    >
                      <div className="flex items-center gap-md">
                        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary-container/20">
                          <Icon size="18px" className="text-primary">history</Icon>
                        </div>
                        <div>
                          <p className="font-body-md font-bold text-on-surface">Version {v.versionNumber}</p>
                          <p className="font-label-md text-on-surface-variant">
                            {v.originalFilename || v.mimeType} · {v.createdAt.slice(0, 10)} · {formatFileSize(v.fileSize)}
                          </p>
                        </div>
                      </div>
                      <span
                        className={`rounded-full px-sm py-0.5 font-label-md ${
                          i === versions.length - 1
                            ? 'bg-tertiary/10 text-tertiary'
                            : 'bg-surface-container-high text-on-surface-variant'
                        }`}
                      >
                        {i === versions.length - 1 ? 'Current' : 'Archived'}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </motion.section>
          </div>

          {/* ─── Sidebar ─── */}
          <motion.div {...reveal} className="space-y-lg">
            <div className="glass-card rounded-xl p-lg">
              <h2 className="mb-lg font-headline-md text-on-surface">Actions</h2>
              <div className="space-y-sm">
                <button
                  onClick={handleOpenChat}
                  className="flex w-full items-center justify-center gap-sm rounded-lg bg-primary py-sm font-body-md font-bold text-on-primary transition-opacity hover:opacity-90"
                >
                  <Icon size="18px">smart_toy</Icon>
                  Open in Chat
                </button>
                <button
                  onClick={handleDelete}
                  disabled={deleting}
                  className="flex w-full items-center justify-center gap-sm rounded-lg border border-error/30 py-sm font-body-md font-bold text-error transition-colors hover:bg-error/10 disabled:opacity-50"
                >
                  <Icon size="18px">delete</Icon>
                  {deleting ? 'Deleting…' : 'Delete Report'}
                </button>
              </div>
            </div>

            <div className="glass-card rounded-xl p-lg">
              <h2 className="mb-lg font-headline-md text-on-surface">Details</h2>
              <div className="space-y-md">
                {[
                  { label: 'Checksum', value: report.checksum || '—' },
                  { label: 'Report ID', value: report.id },
                ].map((row) => (
                  <div key={row.label}>
                    <p className="font-label-md text-[11px] uppercase tracking-wider text-on-surface-variant">
                      {row.label}
                    </p>
                    <p className="mt-sm break-all font-body-md text-on-surface">{row.value}</p>
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
