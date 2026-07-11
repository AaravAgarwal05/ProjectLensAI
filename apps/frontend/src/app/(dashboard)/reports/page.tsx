'use client'

import { motion } from 'framer-motion'
import { DashboardLayout } from '@/components/layout/dashboard-layout'
import { Icon } from '@/components/shared/icon'

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

const filterTabs = ['All Reports', 'Drafts', 'Finalized', 'Archived']

const departments = ['All Departments', 'Compliance', 'Strategy', 'Legal', 'HR', 'Engineering', 'Finance']

const tableReports = [
  {
    name: 'Annual_Risk_Assessment_2024',
    icon: 'description',
    dept: 'Compliance',
    author: 'Sarah Jenkins',
    avatar: null,
    initials: 'SJ',
    version: 'v2.4.1',
    status: 'Published',
    statusColor: 'text-tertiary',
    statusBg: 'bg-tertiary/10',
  },
  {
    name: 'Market_Expansion_Strategy_APAC',
    icon: 'analytics',
    dept: 'Strategy',
    author: 'Marcus Chen',
    avatar: null,
    initials: 'MC',
    version: 'v1.0.0',
    status: 'Drafting',
    statusColor: 'text-primary',
    statusBg: 'bg-primary/10',
    pulsing: true,
  },
  {
    name: 'Legal_Disclosures_Bundle_Q3',
    icon: 'folder_zip',
    dept: 'Legal',
    author: 'A. Lens (AI)',
    avatar: null,
    initials: 'AL',
    version: 'v3.9.0',
    status: 'Archived',
    statusColor: 'text-outline',
    statusBg: 'bg-outline/10',
  },
  {
    name: 'Employee_Engagement_Survey_Data',
    icon: 'description',
    dept: 'HR',
    author: 'Elena Rodriguez',
    avatar: null,
    initials: 'ER',
    version: 'v1.2.0',
    status: 'Published',
    statusColor: 'text-tertiary',
    statusBg: 'bg-tertiary/10',
  },
]

const avatarColors: Record<string, string> = {
  SJ: 'bg-amber-500',
  MC: 'bg-cyan-500',
  AL: 'bg-secondary',
  ER: 'bg-rose-500',
}

const footerCards = [
  {
    icon: 'cloud',
    iconColor: 'text-primary',
    title: 'Storage Used',
    value: '1.2 GB / 10 GB',
    progress: 12,
  },
  {
    icon: 'insights',
    iconColor: 'text-secondary',
    title: 'AI Insights Generated',
    value: '4.8k',
    trend: '+12% this week',
  },
  {
    icon: 'group',
    iconColor: 'text-tertiary',
    title: 'Active Collaborators',
    value: '32',
    avatars: ['#a78bfa', '#f472b6', '#34d399', '#fbbf24'] as string[],
    overflow: 29,
  },
  {
    icon: 'network_check',
    iconColor: 'text-primary',
    title: 'System Latency',
    value: '42ms',
    status: 'All systems operational',
  },
] as const

/* ─── helpers ─── */

function AvatarCircle({ initials, color, size = 'w-7 h-7' }: { initials: string; color: string; size?: string }) {
  return (
    <div className={`${size} rounded-full ${color} flex items-center justify-center font-label-md text-[10px] text-white shrink-0`}>
      {initials}
    </div>
  )
}

function StatusDot({ color, pulsing }: { color: string; pulsing?: boolean }) {
  return (
    <span className={`w-1.5 h-1.5 rounded-full ${color} ${pulsing ? 'animate-pulse' : ''}`} />
  )
}

/* ─── page ─── */

export default function ReportsPage() {
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

        {/* ─── Upload + AI Processing Bento ─── */}
        <motion.div
          className="grid grid-cols-12 gap-gutter mb-xl"
          variants={containerVariants}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true }}
        >
          {/* Upload Drop Zone */}
          <motion.div variants={itemVariants} className="col-span-12 lg:col-span-7">
            <div className="glass-card p-xl rounded-xl flex flex-col items-center justify-center border-dashed border-2 border-outline/30 min-h-[240px] hover:border-primary/50 transition-all group cursor-pointer">
              <div className="w-16 h-16 rounded-full bg-surface-container-highest flex items-center justify-center mb-md group-hover:bg-primary-container group-hover:text-on-primary-container transition-colors">
                <Icon size="30px">cloud_upload</Icon>
              </div>
              <p className="font-headline-md mb-xs text-on-surface">Drop files to initiate Lens analysis</p>
              <p className="text-on-surface-variant font-body-md mb-lg">Supports PDF, DOCX, and ZIP archives (Up to 500MB)</p>
              <div className="flex items-center gap-sm">
                <span className="px-sm py-1 bg-surface-container-high rounded font-label-md border border-outline-variant">PDF</span>
                <span className="px-sm py-1 bg-surface-container-high rounded font-label-md border border-outline-variant">DOCX</span>
                <span className="px-sm py-1 bg-surface-container-high rounded font-label-md border border-outline-variant">ZIP</span>
              </div>
            </div>
          </motion.div>

          {/* AI Processing */}
          <motion.div variants={itemVariants} className="col-span-12 lg:col-span-5">
            <div className="glass-card p-lg rounded-xl">
              {/* Header */}
              <div className="flex items-center justify-between mb-lg">
                <div className="flex items-center gap-sm">
                  <span className="w-2 h-2 rounded-full bg-primary ai-glow animate-pulse" />
                  <span className="font-body-md font-bold text-on-surface">AI Processing</span>
                </div>
                <span className="font-label-md text-primary bg-primary/10 px-2 py-0.5 rounded">2 Active Tasks</span>
              </div>

              {/* Task 1 */}
              <div className="space-y-sm mb-lg">
                <div className="flex items-center justify-between">
                  <span className="font-body-md text-on-surface truncate max-w-[200px]">Q4_Fiscal_Audit_Final.pdf</span>
                  <span className="font-label-md text-primary">82%</span>
                </div>
                <div className="h-1.5 w-full bg-surface-container-highest rounded-full overflow-hidden">
                  <div className="h-full bg-primary ai-glow rounded-full transition-all duration-700" style={{ width: '82%' }} />
                </div>
                <p className="font-label-md text-on-surface-variant italic">Extracting fiscal tables &amp; sentiment analysis...</p>
              </div>

              {/* Task 2 */}
              <div className="space-y-sm">
                <div className="flex items-center justify-between">
                  <span className="font-body-md text-on-surface truncate max-w-[200px]">Legal_Briefing_v2.docx</span>
                  <span className="font-label-md text-secondary">45%</span>
                </div>
                <div className="h-1.5 w-full bg-surface-container-highest rounded-full overflow-hidden">
                  <div className="h-full bg-secondary ai-glow rounded-full transition-all duration-700" style={{ width: '45%' }} />
                </div>
                <p className="font-label-md text-on-surface-variant italic">Cross-referencing liability clauses...</p>
              </div>
            </div>
          </motion.div>
        </motion.div>

        {/* ─── Filters Bar ─── */}
        <motion.div className="flex flex-wrap gap-md items-center mb-lg" {...simpleReveal}>
          {/* Segmented control */}
          <div className="flex items-center gap-sm bg-surface-container-low p-1 rounded-lg border border-outline-variant">
            {filterTabs.map((tab) => (
              <button
                key={tab}
                className={`px-md py-1.5 rounded-md font-body-md transition-colors ${
                  tab === 'All Reports'
                    ? 'bg-primary-container text-on-primary-container font-bold'
                    : 'text-on-surface-variant hover:text-on-surface'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>

          <span className="h-8 w-[1px] bg-outline-variant hidden sm:block" />

          {/* Department select */}
          <select className="bg-surface-container-low border border-outline-variant rounded-lg px-md py-1.5 font-body-md text-on-surface appearance-none cursor-pointer">
            {departments.map((d) => (
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

        {/* ─── Report Table ─── */}
        <motion.div className="glass-card rounded-xl overflow-hidden" variants={containerVariants} initial="hidden" whileInView="show" viewport={{ once: true }}>
          <table className="w-full">
            <thead>
              <tr className="bg-surface-container-highest/50 border-b border-outline-variant">
                {['Name', 'Department', 'Author', 'Version', 'Status', 'Actions'].map((h) => (
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
              {tableReports.map((r) => (
                <motion.tr
                  key={r.name}
                  variants={itemVariants}
                  className="hover:bg-white/5 transition-colors group"
                >
                  {/* Name */}
                  <td className="px-md py-3">
                    <div className="flex items-center gap-sm">
                      <Icon size="20px" className="text-primary shrink-0">{r.icon}</Icon>
                      <div>
                        <p className="font-body-md font-bold text-on-surface">{r.name}</p>
                        <p className="font-label-md text-on-surface-variant">{r.dept}</p>
                      </div>
                    </div>
                  </td>

                  {/* Department */}
                  <td className="px-md py-3">
                    <span className="font-body-md text-on-surface-variant">{r.dept}</span>
                  </td>

                  {/* Author */}
                  <td className="px-md py-3">
                    <div className="flex items-center gap-sm">
                      <AvatarCircle initials={r.initials} color={avatarColors[r.initials] ?? 'bg-surface-container-highest'} />
                      <span className="font-body-md text-on-surface-variant">{r.author}</span>
                    </div>
                  </td>

                  {/* Version */}
                  <td className="px-md py-3">
                    <span className="font-code-sm text-on-surface-variant">{r.version}</span>
                  </td>

                  {/* Status */}
                  <td className="px-md py-3">
                    <div className="flex items-center gap-1.5">
                      <StatusDot color={r.statusColor} pulsing={r.pulsing} />
                      <span className={`font-body-md ${r.statusColor}`}>{r.status}</span>
                    </div>
                  </td>

                  {/* Actions */}
                  <td className="px-md py-3">
                    <div className="flex justify-end gap-xs opacity-0 group-hover:opacity-100 transition-opacity">
                      <button className="flex h-8 w-8 items-center justify-center rounded hover:bg-surface-container-high transition-colors">
                        <Icon size="18px" className="text-on-surface-variant">visibility</Icon>
                      </button>
                      <button className="flex h-8 w-8 items-center justify-center rounded hover:bg-surface-container-high transition-colors">
                        <Icon size="18px" className="text-on-surface-variant">smart_toy</Icon>
                      </button>
                      <button className="flex h-8 w-8 items-center justify-center rounded hover:bg-surface-container-high transition-colors">
                        <Icon size="18px" className="text-on-surface-variant">compare_arrows</Icon>
                      </button>
                      <button className="flex h-8 w-8 items-center justify-center rounded hover:bg-surface-container-high transition-colors">
                        <Icon size="18px" className="text-on-surface-variant">delete</Icon>
                      </button>
                    </div>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>

          {/* ─── Pagination ─── */}
          <div className="flex justify-between items-center px-lg py-md bg-surface-container-low border-t border-outline-variant">
            <span className="font-label-md text-on-surface-variant">Showing 1-10 of 248 entries</span>
            <div className="flex items-center gap-sm">
              <button className="flex h-8 w-8 items-center justify-center rounded hover:bg-surface-container-high transition-colors border border-outline-variant">
                <Icon size="16px" className="text-on-surface-variant">chevron_left</Icon>
              </button>
              <button className="flex h-8 w-8 items-center justify-center rounded bg-primary-container text-on-primary-container transition-colors font-label-md">1</button>
              <button className="flex h-8 w-8 items-center justify-center rounded hover:bg-surface-container-high transition-colors font-label-md text-on-surface-variant">2</button>
              <button className="flex h-8 w-8 items-center justify-center rounded hover:bg-surface-container-high transition-colors font-label-md text-on-surface-variant">3</button>
              <span className="font-label-md text-on-surface-variant px-xs">...</span>
              <button className="flex h-8 w-8 items-center justify-center rounded hover:bg-surface-container-high transition-colors font-label-md text-on-surface-variant">25</button>
              <button className="flex h-8 w-8 items-center justify-center rounded hover:bg-surface-container-high transition-colors border border-outline-variant">
                <Icon size="16px" className="text-on-surface-variant">chevron_right</Icon>
              </button>
            </div>
          </div>
        </motion.div>

        {/* ─── Footer Stats ─── */}
        <motion.div
          className="grid grid-cols-1 md:grid-cols-4 gap-gutter mt-xl"
          variants={containerVariants}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true }}
        >
          {/* Storage Used */}
          <motion.div variants={itemVariants} className="glass-card p-md rounded-xl">
            <div className="flex items-center justify-between mb-sm">
              <span className="font-label-md text-[10px] uppercase text-outline">{footerCards[0].title}</span>
              <Icon size="18px" className={footerCards[0].iconColor}>{footerCards[0].icon}</Icon>
            </div>
            <p className="font-headline-md font-bold text-primary mb-sm">{footerCards[0].value}</p>
            <div className="h-1.5 w-full bg-surface-container-highest rounded-full overflow-hidden">
              <div className="h-full bg-primary rounded-full" style={{ width: '12%' }} />
            </div>
          </motion.div>

          {/* AI Insights */}
          <motion.div variants={itemVariants} className="glass-card p-md rounded-xl">
            <div className="flex items-center justify-between mb-sm">
              <span className="font-label-md text-[10px] uppercase text-outline">{footerCards[1].title}</span>
              <Icon size="18px" className={footerCards[1].iconColor}>{footerCards[1].icon}</Icon>
            </div>
            <p className="font-headline-md font-bold text-secondary mb-sm">{footerCards[1].value}</p>
            <div className="flex items-center gap-1 text-emerald-500 font-label-md text-[11px]">
              <Icon size="14px">trending_up</Icon>
              <span>{footerCards[1].trend}</span>
            </div>
          </motion.div>

          {/* Active Collaborators */}
          <motion.div variants={itemVariants} className="glass-card p-md rounded-xl">
            <div className="flex items-center justify-between mb-sm">
              <span className="font-label-md text-[10px] uppercase text-outline">{footerCards[2].title}</span>
              <Icon size="18px" className={footerCards[2].iconColor}>{footerCards[2].icon}</Icon>
            </div>
            <p className="font-headline-md font-bold text-on-surface mb-sm">{footerCards[2].value}</p>
            <div className="flex items-center">
              <div className="flex -space-x-1.5">
                {footerCards[2].avatars.map((bg, i) => (
                  <div
                    key={i}
                    className="w-6 h-6 rounded-full border-2 border-surface"
                    style={{ backgroundColor: bg }}
                  />
                ))}
              </div>
              <span className="font-label-md text-on-surface-variant ml-sm">+{footerCards[2].overflow} overflow</span>
            </div>
          </motion.div>

          {/* System Latency */}
          <motion.div variants={itemVariants} className="glass-card p-md rounded-xl">
            <div className="flex items-center justify-between mb-sm">
              <span className="font-label-md text-[10px] uppercase text-outline">{footerCards[3].title}</span>
              <Icon size="18px" className={footerCards[3].iconColor}>{footerCards[3].icon}</Icon>
            </div>
            <p className="font-headline-md font-bold text-tertiary mb-sm">{footerCards[3].value}</p>
            <div className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_6px_rgba(34,197,94,0.6)]" />
              <span className="font-label-md text-emerald-500 text-[11px]">{footerCards[3].status}</span>
            </div>
          </motion.div>
        </motion.div>

      </div>
    </DashboardLayout>
  )
}
