'use client'

import { motion } from 'framer-motion'
import { DashboardLayout } from '@/components/layout/dashboard-layout'
import { Icon } from '@/components/shared/icon'

/* ─── animation helpers ─── */

const containerVariants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.07 } },
}

const itemVariants = {
  hidden: { opacity: 0, y: 24 },
  show: { opacity: 1, y: 0, transition: { duration: 0.45, ease: 'easeOut' as const } },
}

const simpleReveal = {
  initial: { opacity: 0, y: 20 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true },
  transition: { duration: 0.45, ease: 'easeOut' as const },
}

/* ─── data ─── */

type CardTheme = 'primary' | 'secondary' | 'tertiary'

interface CollectionCard {
  name: string
  icon: string
  theme: CardTheme
  description: string
  reportCount: number
  time: string
  dashed?: boolean
}

const collections: CollectionCard[] = [
  {
    name: 'System Latency Logs',
    icon: 'folder',
    theme: 'primary',
    description:
      'Historical benchmarking data for real-time inference optimization across edge nodes.',
    reportCount: 12,
    time: '2h ago',
  },
  {
    name: 'Model Drift Analysis',
    icon: 'folder_special',
    theme: 'secondary',
    description:
      'Tracking accuracy degradation in fine-tuned LLM checkpoints over Q3 production cycles.',
    reportCount: 8,
    time: 'Yesterday',
  },
  {
    name: 'Compliance Audits',
    icon: 'folder_open',
    theme: 'tertiary',
    description:
      'Empty collection. Start adding data security reports and bias assessments here.',
    reportCount: 0,
    time: 'Sept 12',
    dashed: true,
  },
  {
    name: 'Semantic Mapping',
    icon: 'topic',
    theme: 'primary',
    description:
      'Vector database performance metrics and cluster visualization exports.',
    reportCount: 24,
    time: '3d ago',
  },
  {
    name: 'Archived Experiments',
    icon: 'folder_zip',
    theme: 'secondary',
    description:
      'Legacy model evaluations from the prototype phase (Pre-deployment).',
    reportCount: 54,
    time: '1mo ago',
  },
]

/* ─── theme helpers ─── */

const themeColors: Record<CardTheme, { iconBg: string; iconColor: string; iconBorder: string; hoverBg: string }> = {
  primary: {
    iconBg: 'bg-primary/10',
    iconColor: 'text-primary',
    iconBorder: 'border-primary/20',
    hoverBg: 'group-hover:bg-primary/15',
  },
  secondary: {
    iconBg: 'bg-secondary/10',
    iconColor: 'text-secondary',
    iconBorder: 'border-secondary/20',
    hoverBg: 'group-hover:bg-secondary/15',
  },
  tertiary: {
    iconBg: 'bg-tertiary/10',
    iconColor: 'text-tertiary',
    iconBorder: 'border-tertiary/20',
    hoverBg: 'group-hover:bg-tertiary/15',
  },
}

/* ─── Collection Card ─── */

function CollectionCard({ card }: { card: CollectionCard }) {
  const t = themeColors[card.theme]
  const borderStyle = card.dashed
    ? 'border-dashed border-2 opacity-60 hover:opacity-100'
    : ''

  return (
    <motion.div variants={itemVariants} className="relative">
      <div
        className={`glass-card group flex flex-col p-md rounded-xl relative cursor-pointer transition-all duration-300
          hover:border-[rgba(192,193,255,0.4)] hover:bg-[rgba(14,14,16,0.9)] hover:-translate-y-0.5
          ${borderStyle}`}
      >
        {/* Top row */}
        <div className="flex justify-between items-start mb-lg">
          <div
            className={`w-12 h-12 rounded-lg border flex items-center justify-center transition-colors ${t.iconBorder} ${t.iconBg} ${t.hoverBg}`}
          >
            <Icon className={t.iconColor}>{card.icon}</Icon>
          </div>

          {/* Hover actions */}
          <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <button className="p-1.5 rounded hover:bg-surface-container-high text-on-surface-variant transition-colors">
              <Icon size="16px">edit</Icon>
            </button>
            <button className="p-1.5 rounded hover:bg-surface-container-high text-on-surface-variant transition-colors">
              <Icon size="16px">delete</Icon>
            </button>
          </div>
        </div>

        {/* Body */}
        <div className="flex-1">
          <h3 className="font-headline-md text-on-surface mb-xs">{card.name}</h3>
          <p className="text-on-surface-variant text-body-md line-clamp-2">{card.description}</p>
        </div>

        {/* Footer */}
        <div className="mt-xl pt-md border-t border-outline-variant flex justify-between">
          <span
            className={`font-label-md text-code-sm ${card.reportCount > 0 ? 'text-primary' : 'text-on-surface-variant'}`}
          >
            {card.reportCount} reports
          </span>
          <span className="font-label-md text-code-sm text-on-surface-variant opacity-60">
            {card.time}
          </span>
        </div>
      </div>
    </motion.div>
  )
}

/* ─── Create Collection Button ─── */

function CreateCollectionButton() {
  return (
    <motion.div variants={itemVariants} className="relative">
      <button className="w-full border-2 border-dashed border-outline-variant rounded-xl flex flex-col items-center justify-center gap-md hover:bg-surface-container-high transition-all group min-h-[220px]">
        <div className="w-12 h-12 rounded-full border border-outline-variant flex items-center justify-center transition-colors group-hover:border-primary group-hover:text-primary">
          <Icon size="24px">add</Icon>
        </div>
        <span className="font-bold text-on-surface-variant transition-colors group-hover:text-on-surface">
          Create Collection
        </span>
      </button>
    </motion.div>
  )
}

/* ─── AI Insight Banner ─── */

function AiInsightBanner() {
  return (
    <motion.div
      variants={itemVariants}
      className="glass-card bg-primary-container/5 border-primary/20 overflow-hidden group col-span-1 md:col-span-2"
    >
      <div className="flex">
        {/* Left: text content */}
        <div className="w-1/2 p-lg flex flex-col justify-between">
          <div>
            {/* Badge */}
            <div className="inline-flex items-center gap-2 bg-primary/10 border border-primary/20 px-2 py-1 rounded mb-md">
              <Icon size="12px" className="text-primary">auto_awesome</Icon>
              <span className="text-primary text-[10px] font-bold tracking-widest uppercase">AI Insight</span>
            </div>

            <h3 className="font-headline-md text-on-surface mb-md">Consolidate Latency Reports?</h3>
            <p className="text-on-surface-variant text-body-md mb-lg">
              High correlation detected between System Latency Logs and Network Stability
              benchmarks. Combine into a unified performance analysis?
            </p>
          </div>

          <div className="flex gap-md">
            <button className="bg-primary text-on-primary font-bold text-code-sm px-md py-2 rounded-lg hover:opacity-90 transition-opacity">
              Actionable View
            </button>
            <button className="border border-outline-variant text-on-surface-variant font-bold text-code-sm px-md py-2 rounded-lg hover:bg-surface-container-high transition-colors">
              Dismiss
            </button>
          </div>
        </div>

        {/* Right: visual */}
        <div className="w-1/2 bg-surface-container-highest flex items-end justify-center p-lg">
          <div className="grid grid-cols-4 gap-2">
            <div className="w-12 h-16 bg-primary border border-primary-container rounded-lg mt-0" />
            <div className="w-12 h-12 bg-primary border border-primary-container rounded-lg mt-4" />
            <div className="w-12 h-20 bg-primary border border-primary-container rounded-lg mt-0" />
            <div className="w-12 h-14 bg-primary border border-primary-container rounded-lg mt-2" />
          </div>
        </div>
      </div>
    </motion.div>
  )
}

/* ─── Page Component ─── */

export default function CollectionsPage() {
  return (
    <DashboardLayout searchPlaceholder="Search collections, tags, or metadata...">
      <div className="p-xl bg-surface relative">
        <div className="max-w-[1440px] mx-auto">
          {/* Background glow */}
          <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-primary/5 rounded-full blur-[120px] -z-10 pointer-events-none" />

          {/* ─── Page Header ─── */}
          <motion.div
            className="flex justify-between items-end mb-xl"
            {...simpleReveal}
          >
            <div>
              <h1 className="font-headline-lg text-on-surface mb-xs">Collections</h1>
              <p className="text-on-surface-variant max-w-xl">
                Organize your AI analysis reports into thematic collections for faster retrieval
                and cross-reference insights.
              </p>
            </div>

            <div className="flex gap-2">
              <button className="p-2 border border-outline-variant rounded hover:bg-surface-container-high transition-colors text-on-surface-variant">
                <Icon size="20px">filter_list</Icon>
              </button>
              <button className="p-2 border border-outline-variant rounded hover:bg-surface-container-high transition-colors text-on-surface-variant">
                <Icon size="20px">grid_view</Icon>
              </button>
            </div>
          </motion.div>

          {/* ─── Grid ─── */}
          <motion.div
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-lg"
            variants={containerVariants}
            initial="hidden"
            whileInView="show"
            viewport={{ once: true }}
          >
            {/* Collection Cards */}
            {collections.map((card) => (
              <CollectionCard key={card.name} card={card} />
            ))}

            {/* AI Insight Banner */}
            <AiInsightBanner />

            {/* Create Collection Button */}
            <CreateCollectionButton />
          </motion.div>
        </div>

        {/* ─── Footer Bar ─── */}
        <motion.div
          className="h-10 border-t border-outline-variant bg-surface-container-lowest px-xl flex items-center justify-between text-code-sm text-on-surface-variant mt-xl"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.4, delay: 0.3 }}
        >
          <div className="flex items-center gap-lg">
            <span className="flex items-center gap-2">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-500 opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
              </span>
              API: Healthy
            </span>
            <span>Total Storage: 1.2GB / 10GB</span>
          </div>
          <span>Build v2.4.0-stable</span>
        </motion.div>
      </div>
    </DashboardLayout>
  )
}
