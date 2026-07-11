'use client'

import { motion } from 'framer-motion'
import Link from 'next/link'
import { DashboardLayout } from '@/components/layout/dashboard-layout'
import { Icon } from '@/components/shared/icon'

/* ─── container stagger helpers ─── */

const containerVariants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.07 } },
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

const metrics = [
  { label: 'Total Reports', value: '1,284', trend: '+12%', icon: 'description', color: 'text-primary' },
  { label: 'Processed', value: '1,241', trend: '98.2%', icon: 'memory', color: 'text-secondary' },
  { label: 'Total Chats', value: '4.8k', trend: null, icon: 'chat_bubble', color: 'text-tertiary' },
  { label: 'Collections', value: '42', trend: null, icon: 'database', color: 'text-primary' },
  { label: 'Pages Indexed', value: '18.5k', trend: null, icon: 'auto_stories', color: 'text-secondary' },
  { label: 'Tokens', value: '1.2M', trend: null, icon: 'generating_tokens', color: 'text-tertiary' },
]

const reports = [
  { name: 'Market_Analysis_Q3.pdf', size: '4.2 MB', dept: 'Financials', status: 'Success', modified: '2023-11-24 14:20', action: 'chat_bubble' },
  { name: 'Product_Spec_V2.docx', size: '1.1 MB', dept: 'Engineering', status: 'Processing', modified: '2023-11-24 13:05', action: 'chat_bubble' },
  { name: 'User_Retention_Logs.csv', size: '15.8 MB', dept: 'Analytics', status: 'Success', modified: '2023-11-23 18:44', action: 'chat_bubble' },
  { name: 'Legal_Compliance_2024.pdf', size: '0.8 MB', dept: 'HR', status: 'Failed', modified: '2023-11-23 15:22', action: 'replay' },
]

const queueItems = [
  { label: 'Parsing', pct: 82, color: 'bg-primary' as const, desc: 'Scanning Financials_Extract.pdf...' },
  { label: 'Chunking', pct: 45, color: 'bg-secondary' as const, desc: 'Optimizing semantic splits...' },
  { label: 'Embedding', pct: 12, color: 'bg-tertiary' as const, desc: 'Llama-3 vectorization...' },
]

const healthServices = [
  { name: 'Ollama', dotColor: 'bg-emerald-500', dotShadow: 'shadow-[0_0_6px_rgba(34,197,94,0.6)]', status: 'Llama3:8b • 2.4ms' },
  { name: 'ChromaDB', dotColor: 'bg-emerald-500', dotShadow: 'shadow-[0_0_6px_rgba(34,197,94,0.6)]', status: 'Vectors: 412k' },
  { name: 'PostgreSQL', dotColor: 'bg-amber-500', dotShadow: 'shadow-[0_0_6px_rgba(245,158,11,0.6)]', status: 'CPU: 62%' },
]

const chats = [
  { title: 'Q4 Financial Summary', time: '2h ago', preview: 'Revenue grew 15% QoQ, driven by Engineering performance and cost-reduction initiatives across all departments.' },
  { title: 'Product vs Market Comparison', time: '5h ago', preview: 'Comparing market positioning across the three competitor analyses in the Strategy collection.' },
  { title: 'Engineering Review Notes', time: '1d ago', preview: 'Key observations from the Q3 Engineering Review — velocity, sprint health, and team sentiment.' },
  { title: 'Compliance Audit Q&A', time: '2d ago', preview: 'Addressing the outstanding compliance gaps identified in the Legal_Compliance_2024 report.' },
]

/* ─── helpers ─── */

function StatusPill({ status }: { status: string }) {
  const cfg: Record<string, { text: string; ring: string }> = {
    Success: { text: 'text-emerald-500', ring: 'ring-emerald-500/30' },
    Processing: { text: 'text-amber-500', ring: 'ring-amber-500/30' },
    Failed: { text: 'text-red-500', ring: 'ring-red-500/30' },
  }
  const s = (cfg[status] ?? cfg.Success) as { text: string; ring: string }
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 font-label-md text-[11px] ring-1 ${s.text} ${s.ring}`}
    >
      {status}
    </span>
  )
}

export default function DashboardPage() {
  return (
    <DashboardLayout>
      <div className="p-xl">
        {/* ─── Page Header ─── */}
        <motion.div className="mb-xl flex items-start justify-between" {...simpleReveal} transition={{ ...simpleReveal.transition, delay: 0 }}>
          <div>
            <h1 className="font-headline-lg font-bold text-on-surface">Intelligence Overview</h1>
            <p className="font-body-md text-on-surface-variant">Real-time status of your neural architecture and document indexing.</p>
          </div>

          {/* System Nominal badge */}
          <div className="glass-card flex items-center gap-sm rounded-lg px-md py-2">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-500 opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
            </span>
            <span className="font-label-md text-[11px] uppercase text-emerald-400">System Nominal</span>
          </div>
        </motion.div>

        {/* ─── Metric Cards ─── */}
        <motion.div
          className="mb-xl grid grid-cols-1 gap-md md:grid-cols-3 lg:grid-cols-6"
          variants={containerVariants}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true }}
        >
          {metrics.map((m) => (
            <motion.div key={m.label} variants={itemVariants} className="glass-card ai-glow rounded-xl p-md">
              <div className="mb-1 flex items-center justify-between">
                <Icon className={m.color} size="18px">{m.icon}</Icon>
                {m.trend && (
                  <span className="font-label-md text-[10px] text-emerald-500">{m.trend}</span>
                )}
              </div>
              <div className="font-display text-headline-md font-bold text-on-surface">{m.value}</div>
              <div className="font-label-md text-[10px] uppercase text-outline">{m.label}</div>
            </motion.div>
          ))}
        </motion.div>

        {/* ─── Main Content Grid ─── */}
        <div className="grid grid-cols-12 gap-xl">

          {/* ─── LEFT COLUMN (8 cols) ─── */}
          <div className="col-span-12 space-y-xl lg:col-span-8">

            {/* Recent Reports */}
            <motion.div {...simpleReveal} transition={{ ...simpleReveal.transition, delay: 0.1 }}>
              <div className="mb-md flex items-center justify-between">
                <h2 className="font-display text-headline-md text-on-surface">Recent Reports</h2>
                <Link href="/reports" className="flex items-center gap-1 font-label-md text-primary hover:underline">
                  View All
                  <Icon size="16px">arrow_forward</Icon>
                </Link>
              </div>

              <div className="glass-card overflow-hidden rounded-xl">
                <table className="w-full">
                  <thead>
                    <tr className="bg-surface-container-high border-b border-outline-variant">
                      <th className="px-md py-3 text-left font-label-md text-[11px] uppercase tracking-wider text-outline">Name</th>
                      <th className="px-md py-3 text-left font-label-md text-[11px] uppercase tracking-wider text-outline">Status</th>
                      <th className="px-md py-3 text-right font-label-md text-[11px] uppercase tracking-wider text-outline">Last Modified</th>
                      <th className="px-md py-3 text-center font-label-md text-[11px] uppercase tracking-wider text-outline">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-outline-variant/30">
                    {reports.map((r) => (
                      <tr key={r.name} className="hover:bg-surface-container-low transition-colors duration-150 group">
                        <td className="px-md py-3">
                          <div className="flex items-center gap-3">
                            <Icon size="20px" className="text-primary shrink-0">description</Icon>
                            <div>
                              <p className="font-body-md font-bold text-on-surface">{r.name}</p>
                              <p className="font-label-md text-[10px] text-outline">{r.size} &bull; {r.dept}</p>
                            </div>
                          </div>
                        </td>
                        <td className="px-md py-3">
                          <StatusPill status={r.status} />
                        </td>
                        <td className="px-md py-3 text-right font-code-sm text-on-surface-variant">{r.modified}</td>
                        <td className="px-md py-3 text-center">
                          <button className="flex h-8 w-8 items-center justify-center rounded hover:bg-primary-container/20 transition-colors mx-auto">
                            <Icon size="18px" className="text-on-surface-variant">{r.action}</Icon>
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </motion.div>

            {/* Processing Queue */}
            <motion.div {...simpleReveal} transition={{ ...simpleReveal.transition, delay: 0.2 }}>
              <h2 className="mb-md font-display text-headline-md text-on-surface">Processing Queue</h2>
              <div className="grid grid-cols-1 gap-md md:grid-cols-3">
                {queueItems.map((q) => (
                  <div key={q.label} className="glass-card rounded-xl p-md">
                    <div className="mb-1 flex items-center justify-between">
                      <span className="font-label-md text-[10px] uppercase text-outline">{q.label}</span>
                      <span className="font-code-sm text-on-surface-variant">{q.pct}%</span>
                    </div>
                    <div className="h-1.5 w-full overflow-hidden rounded-full bg-surface-container-highest">
                      <div
                        className={`h-full rounded-full ${q.color} transition-all duration-700`}
                        style={{ width: `${q.pct}%` }}
                      />
                    </div>
                    <p className="mt-2 text-[10px] italic text-on-surface-variant">{q.desc}</p>
                  </div>
                ))}
              </div>
            </motion.div>
          </div>

          {/* ─── RIGHT COLUMN (4 cols) ─── */}
          <div className="col-span-12 space-y-xl lg:col-span-4">

            {/* AI System Health */}
            <motion.div {...simpleReveal} transition={{ ...simpleReveal.transition, delay: 0.15 }}>
              <h2 className="mb-md font-display text-headline-md text-on-surface">AI System Health</h2>
              <div className="glass-card space-y-4 rounded-xl p-md">
                {healthServices.map((s) => (
                  <div key={s.name} className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span className={`block h-2 w-2 rounded-full ${s.dotColor} ${s.dotShadow}`} />
                      <span className="font-body-md font-bold text-on-surface">{s.name}</span>
                    </div>
                    <span className="font-code-sm text-on-surface-variant">{s.status}</span>
                  </div>
                ))}
              </div>
            </motion.div>

            {/* Recent Chats */}
            <motion.div {...simpleReveal} transition={{ ...simpleReveal.transition, delay: 0.2 }}>
              <div className="mb-md flex items-center justify-between">
                <h2 className="font-display text-headline-md text-on-surface">Recent Chats</h2>
              </div>
              <div className="glass-card custom-scrollbar max-h-[400px] divide-y divide-outline-variant/30 overflow-hidden overflow-y-auto rounded-xl">
                {chats.map((c) => (
                  <div key={c.title} className="group cursor-pointer p-md transition-colors hover:bg-surface-container-high">
                    <div className="flex items-center justify-between">
                      <p className="font-body-md font-bold text-on-surface transition-colors group-hover:text-primary">{c.title}</p>
                      <span className="font-label-md text-[10px] text-outline shrink-0 ml-2">{c.time}</span>
                    </div>
                    <p className="mt-0.5 text-[12px] leading-snug text-on-surface-variant line-clamp-2">{c.preview}</p>
                  </div>
                ))}
              </div>
            </motion.div>

            {/* Active Node Visualization */}
            <motion.div {...simpleReveal} transition={{ ...simpleReveal.transition, delay: 0.25 }}>
              <div className="glass-card group relative flex h-[200px] items-end overflow-hidden rounded-xl">
                {/* Gradient overlay */}
                <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-surface to-transparent" />

                {/* Bottom content */}
                <div className="relative z-10 p-md">
                  <p className="font-label-md text-[10px] uppercase text-primary">Active Node</p>
                  <p className="font-display text-lg font-bold text-on-surface">Neural Core-01</p>
                </div>

                {/* Animated bars */}
                <div className="absolute right-6 bottom-6 flex items-end gap-[3px]">
                  <span className="block w-1 rounded-full bg-primary animate-bounce" style={{ height: '12px', animationDelay: '0s' }} />
                  <span className="block w-1 rounded-full bg-primary animate-bounce" style={{ height: '20px', animationDelay: '0.15s' }} />
                  <span className="block w-1 rounded-full bg-primary animate-bounce" style={{ height: '16px', animationDelay: '0.3s' }} />
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
}
