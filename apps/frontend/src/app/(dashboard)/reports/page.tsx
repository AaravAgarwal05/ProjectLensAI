'use client'

import { useEffect, useState, useCallback, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { DashboardLayout } from '@/components/layout/dashboard-layout'
import { Icon } from '@/components/shared/icon'
import { ReportService } from '@/services/reports'
import { ChatService } from '@/services/chat'
import type { Report, ReportStatus } from '@/types'

/* ─── animation helpers ─── */

const containerVariants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.06 } },
}

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { duration: 0.45, ease: 'easeOut' as const } },
}

const simpleReveal = {
  initial: { opacity: 0, y: 20 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true },
  transition: { duration: 0.45, ease: 'easeOut' as const },
}

/* ─── data ─── */

const FILTER_TABS = [
  { label: 'All Reports', value: undefined as ReportStatus | undefined },
  { label: 'Draft', value: 'draft' as ReportStatus },
  { label: 'Ready', value: 'ready' as ReportStatus },
  { label: 'Archived', value: 'deleted' as ReportStatus },
]

const DEPARTMENTS = ['All Departments', 'Compliance', 'Strategy', 'Legal', 'HR', 'Engineering', 'Finance']

/* ─── helpers ─── */

function getInitials(name: string): string {
  return name
    .split(' ')
    .map((n) => n[0])
    .filter(Boolean)
    .slice(0, 2)
    .join('')
    .toUpperCase()
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}

function statusConfig(status: string) {
  const lower = status.toLowerCase()
  if (lower === 'ready' || lower === 'published')
    return { color: 'text-tertiary', bg: 'bg-tertiary/10', dot: 'bg-tertiary' }
  if (lower === 'draft' || lower === 'uploading' || lower === 'processing')
    return { color: 'text-primary', bg: 'bg-primary/10', dot: 'bg-primary', pulsing: true }
  if (lower === 'archived' || lower === 'deleted')
    return { color: 'text-outline', bg: 'bg-outline/10', dot: 'bg-outline' }
  return { color: 'text-error', bg: 'bg-error/10', dot: 'bg-error' }
}

function avatarBg(name: string): string {
  const colors = ['bg-amber-500', 'bg-cyan-500', 'bg-rose-500', 'bg-violet-500', 'bg-emerald-500', 'bg-pink-500']
  let hash = 0
  for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash)
  return colors[Math.abs(hash) % colors.length] ?? 'bg-surface-container-highest'
}

function shortenTitle(title: string, max = 32): string {
  return title.length > max ? title.slice(0, max) + '…' : title
}

/* ─── page ─── */

export default function ReportsPage() {
  const [reports, setReports] = useState<Report[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [activeTab, setActiveTab] = useState<string | undefined>(undefined)
  const [deptFilter, setDeptFilter] = useState('All Departments')

  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState('')
  const [dragOver, setDragOver] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const router = useRouter()

  const fetchReports = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const status = activeTab as ReportStatus | undefined
      const result = await ReportService.list({
        page,
        pageSize,
        status,
      })
      setReports(result.items)
      setTotal(result.total)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load reports')
      setReports([])
      setTotal(0)
    } finally {
      setLoading(false)
    }
  }, [page, pageSize, activeTab])

  const handleUpload = useCallback(async (file: File) => {
    setUploadError('')
    setUploading(true)
    try {
      await ReportService.upload(file)
      // Refresh list after upload
      fetchReports()
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Upload failed'
      setUploadError(msg)
    } finally {
      setUploading(false)
    }
  }, [fetchReports])

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]
    if (f) handleUpload(f)
    // Reset so same file can be picked again
    e.target.value = ''
  }, [handleUpload])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const f = e.dataTransfer.files?.[0]
    if (f) handleUpload(f)
  }, [handleUpload])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(true)
  }, [])

  const handleDragLeave = useCallback(() => {
    setDragOver(false)
  }, [])

  useEffect(() => {
    fetchReports()
  }, [fetchReports])

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this report permanently?')) return
    try {
      await ReportService.delete(id)
      fetchReports()
    } catch {
      // swallow
    }
  }

  const totalPages = Math.ceil(total / pageSize)

  const handleOpenChat = useCallback(async (reportId: string, reportTitle: string) => {
    try {
      const session = await ChatService.createSession({
        title: reportTitle,
        reportIds: [reportId],
        mode: 'single',
      })
      router.push(`/chat/${session.id}`)
    } catch {
      alert('Failed to create chat session. Please try again.')
    }
  }, [router])

  return (
    <DashboardLayout searchPlaceholder="Search reports, metadata, or AI insights...">
      <div className="p-xl max-w-[1400px] mx-auto">
        {/* ─── Page Header ─── */}
        <motion.div className="flex flex-col sm:flex-row justify-between items-start sm:items-end mb-xl gap-md" {...simpleReveal}>
          <div>
            <h1 className="font-display text-headline-lg text-primary mb-xs">Intellectual Assets</h1>
            <p className="text-on-surface-variant font-body-lg">
              Manage, analyze, and automate reporting across all corporate departments.
            </p>
          </div>
          <div className="flex items-center gap-sm shrink-0">
            <button className="flex items-center gap-xs px-md py-2 border border-outline-variant rounded-lg hover:bg-surface-container-high transition-colors font-body-md">
              <Icon size="18px">filter_list</Icon>
              Advanced Filters
            </button>
            <button className="flex items-center gap-xs px-md py-2 border border-outline-variant rounded-lg hover:bg-surface-container-high transition-colors font-body-md">
              <Icon size="18px">download</Icon>
              Export CSV
            </button>
          </div>
        </motion.div>

        {/* ─── Upload Drop Zone ─── */}
        <motion.div className="col-span-12 lg:col-span-7 mb-xl" {...simpleReveal}>
          <div
            onClick={() => fileInputRef.current?.click()}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            className={`glass-card p-xl rounded-xl flex flex-col items-center justify-center border-dashed border-2 min-h-[160px] transition-all group cursor-pointer ${
              dragOver
                ? 'border-primary bg-primary-container/10'
                : 'border-outline/30 hover:border-primary/50'
            } ${uploading ? 'pointer-events-none opacity-60' : ''}`}
          >
            {/* Hidden file input */}
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx,.zip"
              className="hidden"
              onChange={handleFileSelect}
            />

            {uploading ? (
              <>
                <span className="inline-block h-10 w-10 animate-spin rounded-full border-2 border-primary border-t-transparent mb-md" />
                <p className="font-headline-md mb-xs text-on-surface">Uploading and analyzing…</p>
                <p className="text-on-surface-variant font-body-md">File is being processed. This may take a minute.</p>
              </>
            ) : (
              <>
                <div className="w-14 h-14 rounded-full bg-surface-container-highest flex items-center justify-center mb-md group-hover:bg-primary-container group-hover:text-on-primary-container transition-colors">
                  <Icon size="26px">cloud_upload</Icon>
                </div>
                <p className="font-headline-md mb-xs text-on-surface">
                  {dragOver ? 'Drop file to upload' : 'Drop files to initiate Lens analysis'}
                </p>
                <p className="text-on-surface-variant font-body-md mb-lg">Supports PDF, DOCX, and ZIP archives (Up to 500MB)</p>
                <div className="flex items-center gap-sm">
                  <span className="px-sm py-1 bg-surface-container-high rounded font-label-md border border-outline-variant">PDF</span>
                  <span className="px-sm py-1 bg-surface-container-high rounded font-label-md border border-outline-variant">DOCX</span>
                  <span className="px-sm py-1 bg-surface-container-high rounded font-label-md border border-outline-variant">ZIP</span>
                </div>
              </>
            )}
          </div>
          {uploadError && (
            <motion.p
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-sm font-body-md text-error flex items-center gap-xs"
            >
              <Icon size="16px">error</Icon>
              {uploadError}
            </motion.p>
          )}
        </motion.div>

        {/* ─── Filters Bar ─── */}
        <motion.div className="flex flex-wrap gap-md items-center mb-lg" {...simpleReveal}>
          {/* Segmented control */}
          <div className="flex items-center gap-sm bg-surface-container-low p-1 rounded-lg border border-outline-variant">
            {FILTER_TABS.map((tab) => (
              <button
                key={tab.label}
                onClick={() => { setActiveTab(tab.value); setPage(1) }}
                className={`px-md py-1.5 rounded-md font-body-md transition-colors ${
                  activeTab === tab.value
                    ? 'bg-primary-container text-on-primary-container font-bold'
                    : 'text-on-surface-variant hover:text-on-surface'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <span className="h-8 w-[1px] bg-outline-variant hidden sm:block" />

          {/* Department select */}
          <select
            className="bg-surface-container-low border border-outline-variant rounded-lg px-md py-1.5 font-body-md text-on-surface appearance-none cursor-pointer"
            value={deptFilter}
            onChange={(e) => setDeptFilter(e.target.value)}
          >
            {DEPARTMENTS.map((d) => (
              <option key={d}>{d}</option>
            ))}
          </select>

          {/* Sort select */}
          <select className="bg-surface-container-low border border-outline-variant rounded-lg px-md py-1.5 font-body-md text-on-surface appearance-none cursor-pointer">
            <option>Most Recent</option>
            <option>Alphabetical</option>
            <option>Size</option>
          </select>
        </motion.div>

        {/* ─── Loading ─── */}
        {loading && (
          <div className="flex items-center justify-center py-32">
            <div className="flex flex-col items-center gap-md">
              <span className="inline-block h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
              <p className="font-body-md text-on-surface-variant">Loading reports…</p>
            </div>
          </div>
        )}

        {/* ─── Error ─── */}
        {error && !loading && (
          <div className="flex items-center justify-center py-32">
            <div className="glass-card max-w-md rounded-xl p-xl text-center">
              <Icon className="text-error mb-md" size="40px">error_outline</Icon>
              <h2 className="font-headline-md text-on-surface mb-sm">Failed to load reports</h2>
              <p className="font-body-md text-on-surface-variant mb-lg">{error}</p>
              <button
                onClick={fetchReports}
                className="rounded-lg bg-primary px-lg py-sm font-headline-md text-on-primary transition-colors hover:bg-primary-fixed-dim"
              >
                Try Again
              </button>
            </div>
          </div>
        )}

        {/* ─── Empty State ─── */}
        {!loading && !error && reports.length === 0 && (
          <div className="flex items-center justify-center py-32">
            <div className="max-w-md text-center">
              <Icon className="text-outline mb-md" size="48px">description</Icon>
              <h2 className="font-headline-md text-on-surface mb-sm">No reports yet</h2>
              <p className="font-body-md text-on-surface-variant mb-lg">
                Upload your first report to start analyzing with AI.
              </p>
            </div>
          </div>
        )}

        {/* ─── Report Table ─── */}
        {!loading && !error && reports.length > 0 && (
          <motion.div className="glass-card rounded-xl overflow-hidden" variants={containerVariants} initial="hidden" whileInView="show" viewport={{ once: true }}>
            <table className="w-full">
              <thead>
                <tr className="bg-surface-container-highest/50 border-b border-outline-variant">
                  {['Name', 'Department', 'Author', 'Size', 'Status', 'Actions'].map((h) => (
                    <th
                      key={h}
                      className={`px-md py-3 font-headline-md text-[14px] font-bold uppercase tracking-wider text-on-surface-variant text-left ${
                        h === 'Actions' ? 'text-right' : ''
                      }`}
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-outline-variant">
                {reports.map((r) => {
                  const status = statusConfig(r.status)
                  const initials = getInitials(r.author ?? r.title)
                  return (
                    <motion.tr
                      key={r.id}
                      variants={itemVariants}
                      className="hover:bg-white/5 transition-colors group"
                    >
                      {/* Name */}
                      <td className="px-md py-3">
                        <div className="flex items-center gap-sm">
                          <Icon size="20px" className="text-primary shrink-0">description</Icon>
                          <div>
                            <p className="font-body-md font-bold text-on-surface">{shortenTitle(r.title)}</p>
                            {r.description && (
                              <p className="font-label-md text-on-surface-variant max-w-[240px] truncate">{r.description}</p>
                            )}
                          </div>
                        </div>
                      </td>

                      {/* Department */}
                      <td className="px-md py-3">
                        <span className="font-body-md text-on-surface-variant">{r.department ?? '—'}</span>
                      </td>

                      {/* Author */}
                      <td className="px-md py-3">
                        <div className="flex items-center gap-sm">
                          <div className={`w-7 h-7 rounded-full ${avatarBg(r.author ?? r.title)} flex items-center justify-center font-label-md text-[10px] text-white shrink-0`}>
                            {initials}
                          </div>
                          <span className="font-body-md text-on-surface-variant">{r.author ?? 'Unknown'}</span>
                        </div>
                      </td>

                      {/* Size */}
                      <td className="px-md py-3">
                        <span className="font-code-sm text-on-surface-variant">
                          {r.fileSize ? formatFileSize(r.fileSize) : '—'}
                        </span>
                      </td>

                      {/* Status */}
                      <td className="px-md py-3">
                        <div className="flex items-center gap-1.5">
                          <span className={`w-1.5 h-1.5 rounded-full ${status.dot} ${status.pulsing ? 'animate-pulse' : ''}`} />
                          <span className={`font-body-md capitalize ${status.color}`}>{r.status}</span>
                        </div>
                      </td>

                      {/* Actions */}
                      <td className="px-md py-3">
                        <div className="flex justify-end gap-xs opacity-0 group-hover:opacity-100 transition-opacity">
                          <button className="flex h-8 w-8 items-center justify-center rounded hover:bg-surface-container-high transition-colors">
                            <Icon size="18px" className="text-on-surface-variant">visibility</Icon>
                          </button>
                          <button
                            onClick={() => handleOpenChat(r.id, r.title)}
                            className="flex h-8 w-8 items-center justify-center rounded hover:bg-surface-container-high transition-colors"
                            title="Chat with document"
                          >
                            <Icon size="18px" className="text-on-surface-variant">smart_toy</Icon>
                          </button>
                          <button className="flex h-8 w-8 items-center justify-center rounded hover:bg-surface-container-high transition-colors">
                            <Icon size="18px" className="text-on-surface-variant">compare_arrows</Icon>
                          </button>
                          <button
                            onClick={() => handleDelete(r.id)}
                            className="flex h-8 w-8 items-center justify-center rounded hover:bg-error/10 transition-colors"
                          >
                            <Icon size="18px" className="text-error">delete</Icon>
                          </button>
                        </div>
                      </td>
                    </motion.tr>
                  )
                })}
              </tbody>
            </table>

            {/* ─── Pagination ─── */}
            {total > pageSize && (
              <div className="flex justify-between items-center px-lg py-md bg-surface-container-low border-t border-outline-variant">
                <span className="font-label-md text-on-surface-variant">
                  Showing {Math.min((page - 1) * pageSize + 1, total)}-{Math.min(page * pageSize, total)} of {total} entries
                </span>
                <div className="flex items-center gap-sm">
                  <button
                    onClick={() => setPage(Math.max(1, page - 1))}
                    disabled={page <= 1}
                    className="flex h-8 w-8 items-center justify-center rounded hover:bg-surface-container-high transition-colors border border-outline-variant disabled:opacity-30 disabled:cursor-not-allowed"
                  >
                    <Icon size="16px" className="text-on-surface-variant">chevron_left</Icon>
                  </button>
                  {Array.from({ length: Math.min(totalPages, 7) }, (_, i) => {
                    let pageNum: number
                    if (totalPages <= 7) {
                      pageNum = i + 1
                    } else if (page <= 4) {
                      pageNum = i + 1
                    } else if (page >= totalPages - 3) {
                      pageNum = totalPages - 6 + i
                    } else {
                      pageNum = page - 3 + i
                    }
                    return (
                      <button
                        key={pageNum}
                        onClick={() => setPage(pageNum)}
                        className={`flex h-8 w-8 items-center justify-center rounded transition-colors font-label-md ${
                          page === pageNum
                            ? 'bg-primary-container text-on-primary-container'
                            : 'hover:bg-surface-container-high text-on-surface-variant'
                        }`}
                      >
                        {pageNum}
                      </button>
                    )
                  })}
                  <button
                    onClick={() => setPage(Math.min(totalPages, page + 1))}
                    disabled={page >= totalPages}
                    className="flex h-8 w-8 items-center justify-center rounded hover:bg-surface-container-high transition-colors border border-outline-variant disabled:opacity-30 disabled:cursor-not-allowed"
                  >
                    <Icon size="16px" className="text-on-surface-variant">chevron_right</Icon>
                  </button>
                </div>
              </div>
            )}
          </motion.div>
        )}
      </div>
    </DashboardLayout>
  )
}
