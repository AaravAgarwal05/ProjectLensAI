'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import { motion } from 'framer-motion'
import { DashboardLayout } from '@/components/layout/dashboard-layout'
import { Icon } from '@/components/shared/icon'

/* ─── animation helpers ─── */

const fadeUp = {
  initial: { opacity: 0, y: 20 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true },
  transition: { duration: 0.4, ease: 'easeOut' as const },
}

const containerStagger = {
  hidden: {},
  show: { transition: { staggerChildren: 0.06 } },
}

const itemStagger = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.35, ease: 'easeOut' as const } },
}

/* ─── tab config ─── */

type TabId = 'profile' | 'ai' | 'appearance' | 'system'

interface TabDef {
  id: TabId
  label: string
  icon: string
}

const TABS: TabDef[] = [
  { id: 'profile', label: 'Profile', icon: 'person' },
  { id: 'ai', label: 'AI Configuration', icon: 'automation' },
  { id: 'appearance', label: 'Appearance', icon: 'palette' },
  { id: 'system', label: 'System Status', icon: 'monitoring' },
]

/* ─── main component ─── */

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<TabId>('profile')
  const [activeTheme, setActiveTheme] = useState<string>('Deep Obsidian')
  const [accentColor, setAccentColor] = useState<string>('#c0c1ff')
  const [highDensity, setHighDensity] = useState<boolean>(false)
  const tabBarRef = useRef<HTMLDivElement>(null)
  const [indicatorStyle, setIndicatorStyle] = useState({ width: 0, left: 0 })
  const btnRefs = useRef<Record<string, HTMLButtonElement | null>>({})

  const setBtnRef = useCallback((id: string) => (el: HTMLButtonElement | null) => {
    btnRefs.current[id] = el
  }, [])

  useEffect(() => {
    const btn = btnRefs.current[activeTab]
    if (btn) {
      setIndicatorStyle({ width: btn.offsetWidth, left: btn.offsetLeft })
    }
  }, [activeTab])

  /* ─── tab content ─── */

  function renderContent() {
    switch (activeTab) {
      case 'profile':
        return <ProfileTab />
      case 'ai':
        return <AIConfigTab />
      case 'appearance':
        return (
          <AppearanceTab
            activeTheme={activeTheme}
            setActiveTheme={setActiveTheme}
            accentColor={accentColor}
            setAccentColor={setAccentColor}
            highDensity={highDensity}
            setHighDensity={setHighDensity}
          />
        )
      case 'system':
        return <SystemStatusTab />
    }
  }

  return (
    <DashboardLayout searchPlaceholder="Search settings or tools...">
      <div className="mx-auto w-full max-w-6xl p-xl pb-32 flex flex-col gap-xl">
        {/* ─── Page Header ─── */}
        <motion.div {...fadeUp}>
          <h1 className="font-display font-headline-lg text-primary">System Settings</h1>
          <p className="font-body-md text-on-surface-variant">
            Configure your intelligence workspace, identity, and AI processing parameters.
          </p>
        </motion.div>

        {/* ─── Tab Navigation ─── */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.4, delay: 0.1 }}
          className="relative"
        >
          <div
            ref={tabBarRef}
            className="flex items-center overflow-x-auto whitespace-nowrap border-b border-outline-variant/30"
          >
            {TABS.map((tab) => {
              const isActive = activeTab === tab.id
              return (
                <button
                  key={tab.id}
                  id={`btn-${tab.id}`}
                  ref={setBtnRef(tab.id)}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-lg py-md font-body-md transition-colors ${
                    isActive
                      ? 'font-bold text-primary'
                      : 'text-on-surface-variant hover:text-on-surface'
                  }`}
                >
                  <Icon size="18px">{tab.icon}</Icon>
                  {tab.label}
                </button>
              )
            })}
            {/* animated underline indicator */}
            <div
              className="absolute bottom-0 h-[2px] bg-primary transition-all duration-300 ease-out"
              style={{ width: indicatorStyle.width, left: indicatorStyle.left }}
            />
          </div>
        </motion.div>

        {/* ─── Tab Content ─── */}
        <motion.div
          key={activeTab}
          variants={containerStagger}
          initial="hidden"
          animate="show"
        >
          {renderContent()}
        </motion.div>
      </div>

      {/* ─── Bottom Action Bar ─── */}
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.6 }}
        className="fixed bottom-8 left-1/2 z-50 w-[calc(100%-320px)] max-w-4xl -translate-x-1/2"
      >
        <div className="glass-card flex items-center justify-between rounded-full border border-primary/20 p-md shadow-2xl">
          <div className="flex items-center gap-2">
            <Icon className="text-primary" size="20px">
              info
            </Icon>
            <span className="font-body-md text-on-surface-variant">Unsaved changes detected.</span>
          </div>
          <div className="flex items-center gap-sm">
            <button className="rounded-full px-lg py-sm font-body-md text-on-surface-variant transition-colors hover:text-on-surface">
              Discard
            </button>
            <button className="rounded-full bg-primary px-lg py-sm font-body-md font-bold text-on-primary transition-opacity hover:opacity-90">
              Save Changes
            </button>
          </div>
        </div>
      </motion.div>
    </DashboardLayout>
  )
}

/* ═══════════════════════════════════════════════════
   PROFILE TAB
   ═══════════════════════════════════════════════════ */

function ProfileTab() {
  return (
    <div className="grid grid-cols-1 gap-lg md:grid-cols-3">
      {/* Left Column */}
      <motion.div variants={itemStagger} className="md:col-span-1">
        <h2 className="mb-xs font-headline-md text-on-surface">Personal Identity</h2>
        <p className="font-body-md text-sm text-on-surface-variant">
          Manage your display name, avatar, and contact information used across the workspace.
        </p>
      </motion.div>

      {/* Right Column */}
      <motion.div variants={itemStagger} className="flex flex-col gap-lg md:col-span-2">
        {/* Avatar Card */}
        <div className="glass-card flex items-center gap-xl rounded-xl p-lg">
          <div className="group relative h-24 w-24 shrink-0">
            {/* Avatar */}
            <div className="h-24 w-24 rounded-full border-2 border-primary-container/30 bg-surface-container-high" />
            {/* Hover overlay */}
            <div className="absolute inset-0 flex cursor-pointer items-center justify-center rounded-full bg-black/50 opacity-0 transition-opacity group-hover:opacity-100">
              <Icon className="text-on-surface" size="24px">
                photo_camera
              </Icon>
            </div>
          </div>
          <div className="flex items-center gap-md">
            <button className="rounded-full bg-primary px-lg py-sm font-body-md font-bold text-on-primary transition-opacity hover:opacity-90">
              Change Photo
            </button>
            <button className="rounded-full border border-outline-variant px-lg py-sm font-body-md text-on-surface-variant transition-colors hover:text-on-surface">
              Remove
            </button>
          </div>
        </div>

        {/* Form Card */}
        <div className="glass-card flex flex-col gap-lg rounded-xl p-lg">
          {/* 2-col grid */}
          <div className="grid grid-cols-2 gap-lg">
            <div className="flex flex-col gap-sm">
              <label className="font-label-md text-[11px] uppercase text-outline">Full Name</label>
              <input
                defaultValue="Alex Chen"
                className="w-full rounded-lg border border-outline-variant bg-surface-container-low px-sm py-sm font-body-md text-on-surface outline-none transition-colors focus:border-primary"
              />
            </div>
            <div className="flex flex-col gap-sm">
              <label className="font-label-md text-[11px] uppercase text-outline">Role</label>
              <input
                defaultValue="Senior ML Engineer"
                className="w-full rounded-lg border border-outline-variant bg-surface-container-low px-sm py-sm font-body-md text-on-surface outline-none transition-colors focus:border-primary"
              />
            </div>
          </div>
          {/* Full width */}
          <div className="flex flex-col gap-sm">
            <label className="font-label-md text-[11px] uppercase text-outline">Email Address</label>
            <input
              defaultValue="alex.chen@projectlens.ai"
              className="w-full rounded-lg border border-outline-variant bg-surface-container-low px-sm py-sm font-body-md text-on-surface outline-none transition-colors focus:border-primary"
            />
          </div>
        </div>
      </motion.div>
    </div>
  )
}

/* ═══════════════════════════════════════════════════
   AI CONFIGURATION TAB
   ═══════════════════════════════════════════════════ */

function AIConfigTab() {
  const [embedding, setEmbedding] = useState<'lens' | 'ada'>('lens')
  const [retrieval, setRetrieval] = useState<'hybrid' | 'reranked'>('hybrid')

  return (
    <div className="grid grid-cols-1 gap-lg md:grid-cols-3">
      {/* Left Column */}
      <motion.div variants={itemStagger} className="md:col-span-1">
        <h2 className="mb-xs font-headline-md text-on-surface">Model Orchestration</h2>
        <p className="font-body-md text-sm text-on-surface-variant">
          Select your preferred LLM engine, embedding provider, and retrieval strategy for intelligent queries.
        </p>
      </motion.div>

      {/* Right Column */}
      <motion.div variants={itemStagger} className="md:col-span-2">
        <div className="ai-glow glass-card flex flex-col gap-lg rounded-xl p-lg">
          {/* LLM Model Engine */}
          <div className="flex flex-col gap-sm">
            <div className="flex items-center gap-2">
              <Icon className="text-primary" size="18px">
                auto_awesome
              </Icon>
              <label className="font-label-md text-primary">LLM Model Engine</label>
            </div>
            <select className="w-full rounded-lg border border-outline-variant bg-surface-container-low px-sm py-sm font-body-md text-on-surface outline-none transition-colors focus:border-primary">
              <option>Lens-Ultra-4</option>
              <option>GPT-4o</option>
              <option>Claude 3.5 Sonnet</option>
              <option>Llama-3-70B</option>
            </select>
          </div>

          {/* Embedding Provider */}
          <div className="flex flex-col gap-sm">
            <label className="font-label-md text-[11px] uppercase text-outline">Embedding Provider</label>
            <div className="grid grid-cols-2 gap-sm">
              <button
                onClick={() => setEmbedding('lens')}
                className={`flex items-center gap-2 rounded-lg border px-md py-sm font-body-md transition-colors ${
                  embedding === 'lens'
                    ? 'border-primary bg-primary-container/10 text-primary'
                    : 'border-outline-variant text-on-surface-variant hover:text-on-surface'
                }`}
              >
                <Icon size="18px" fill={embedding === 'lens'}>
                  check_circle
                </Icon>
                Lens-Vector-v2
              </button>
              <button
                onClick={() => setEmbedding('ada')}
                className={`flex items-center gap-2 rounded-lg border px-md py-sm font-body-md transition-colors ${
                  embedding === 'ada'
                    ? 'border-primary bg-primary-container/10 text-primary'
                    : 'border-outline-variant text-on-surface-variant hover:text-on-surface'
                }`}
              >
                <Icon size="18px" fill={embedding === 'ada'}>
                  check_circle
                </Icon>
                Ada-002
              </button>
            </div>
          </div>

          {/* Retrieval Strategy */}
          <div className="flex flex-col gap-sm">
            <label className="font-label-md text-[11px] uppercase text-outline">Retrieval Strategy</label>
            <div className="flex flex-col gap-sm">
              <label
                onClick={() => setRetrieval('hybrid')}
                className={`flex cursor-pointer items-start gap-3 rounded-lg border px-md py-sm transition-colors ${
                  retrieval === 'hybrid'
                    ? 'border-primary bg-primary-container/10'
                    : 'border-outline-variant'
                }`}
              >
                <div className="mt-0.5">
                  <div
                    className={`flex h-5 w-5 items-center justify-center rounded-full border-2 ${
                      retrieval === 'hybrid' ? 'border-primary' : 'border-outline-variant'
                    }`}
                  >
                    {retrieval === 'hybrid' && (
                      <div className="h-2.5 w-2.5 rounded-full bg-primary" />
                    )}
                  </div>
                </div>
                <div>
                  <p className="font-body-md font-bold text-on-surface">Hybrid Semantic Search</p>
                  <p className="font-body-md text-sm text-on-surface-variant">
                    Combines keyword and vector search for balanced retrieval accuracy.
                  </p>
                </div>
              </label>
              <label
                onClick={() => setRetrieval('reranked')}
                className={`flex cursor-pointer items-start gap-3 rounded-lg border px-md py-sm transition-colors ${
                  retrieval === 'reranked'
                    ? 'border-primary bg-primary-container/10'
                    : 'border-outline-variant'
                }`}
              >
                <div className="mt-0.5">
                  <div
                    className={`flex h-5 w-5 items-center justify-center rounded-full border-2 ${
                      retrieval === 'reranked' ? 'border-primary' : 'border-outline-variant'
                    }`}
                  >
                    {retrieval === 'reranked' && (
                      <div className="h-2.5 w-2.5 rounded-full bg-primary" />
                    )}
                  </div>
                </div>
                <div>
                  <p className="font-body-md font-bold text-on-surface">Reranked Top-K</p>
                  <p className="font-body-md text-sm text-on-surface-variant">
                    Uses cross-encoder reranking on top-K results for maximum precision.
                  </p>
                </div>
              </label>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  )
}

/* ═══════════════════════════════════════════════════
   APPEARANCE TAB
   ═══════════════════════════════════════════════════ */

const THEMES = [
  { name: 'Deep Obsidian', colors: ['#131315', '#1c1b1d', '#c0c1ff'] },
  { name: 'Modern Zinc', colors: ['#18181b', '#27272a', '#a1a1aa'] },
  { name: 'Crystal Light', colors: ['#fafafa', '#f4f4f5', '#18181b'] },
]

const ACCENTS = ['#c0c1ff', '#ddb7ff', '#89ceff', '#ffb4ab', '#4ade80']

function AppearanceTab({
  activeTheme,
  setActiveTheme,
  accentColor,
  setAccentColor,
  highDensity,
  setHighDensity,
}: {
  activeTheme: string
  setActiveTheme: (v: string) => void
  accentColor: string
  setAccentColor: (v: string) => void
  highDensity: boolean
  setHighDensity: (v: boolean) => void
}) {
  return (
    <div className="grid grid-cols-1 gap-lg md:grid-cols-3">
      {/* Left Column */}
      <motion.div variants={itemStagger} className="md:col-span-1">
        <h2 className="mb-xs font-headline-md text-on-surface">Visual Workspace</h2>
        <p className="font-body-md text-sm text-on-surface-variant">
          Customize the look and feel of your dashboard including theme, accent color, and density.
        </p>
      </motion.div>

      {/* Right Column */}
      <motion.div variants={itemStagger} className="flex flex-col gap-lg md:col-span-2">
        {/* Color Theme */}
        <div className="glass-card flex flex-col gap-lg rounded-xl p-lg">
          <label className="font-label-md text-[11px] uppercase text-outline">Color Theme</label>
          <div className="grid grid-cols-3 gap-md">
            {THEMES.map((t) => {
              const isActive = activeTheme === t.name
              return (
                <button
                  key={t.name}
                  onClick={() => setActiveTheme(t.name)}
                  className={`overflow-hidden rounded-xl transition-all ${
                    isActive
                      ? 'border-2 border-primary ring-1 ring-primary/30'
                      : 'border border-outline-variant hover:border-outline'
                  }`}
                >
                  {/* Color Preview */}
                  <div className="flex h-16 items-end gap-[2px] p-2" style={{ background: t.colors[0] }}>
                    <div className="h-4 flex-1 rounded-t-sm" style={{ background: t.colors[1] }} />
                    <div className="h-8 flex-1 rounded-t-sm" style={{ background: t.colors[1] }} />
                    <div className="h-6 flex-1 rounded-t-sm" style={{ background: t.colors[1] }} />
                    <div className="h-2 flex-1 rounded-t-sm" style={{ background: t.colors[1] }} />
                    <span className="ml-auto block rounded-full px-1 text-[8px] font-bold" style={{ background: t.colors[2], color: t.colors[0] }}>
                      A
                    </span>
                  </div>
                  <div className="bg-surface-container-low px-sm py-2 text-left">
                    <p className="font-body-md text-xs font-bold text-on-surface">{t.name}</p>
                  </div>
                </button>
              )
            })}
          </div>
        </div>

        {/* Accent Core */}
        <div className="glass-card flex flex-col gap-lg rounded-xl p-lg">
          <label className="font-label-md text-[11px] uppercase text-outline">Accent Core</label>
          <div className="flex items-center gap-md">
            {ACCENTS.map((color) => {
              const isActive = accentColor === color
              return (
                <button
                  key={color}
                  onClick={() => setAccentColor(color)}
                  className={`h-10 w-10 rounded-full transition-all ${
                    isActive
                      ? 'ring-4 ring-[#c0c1ff]/20 ring-offset-2 ring-offset-surface'
                      : 'hover:scale-110'
                  }`}
                  style={{ background: color }}
                />
              )
            })}
          </div>
        </div>

        {/* High Density Mode Toggle */}
        <div className="glass-card flex flex-col gap-lg rounded-xl p-lg">
          <div className="flex items-center justify-between rounded-lg bg-surface-container-low p-md">
            <div>
              <p className="font-body-md font-bold text-on-surface">High Density Mode</p>
              <p className="font-body-md text-sm text-on-surface-variant">
                Compact spacing for power users who want more data on screen.
              </p>
            </div>
            {/* Toggle */}
            <button
              onClick={() => setHighDensity(!highDensity)}
              className={`relative h-6 w-12 rounded-full transition-colors ${
                highDensity ? 'bg-primary' : 'bg-outline-variant'
              }`}
            >
              <span
                className={`absolute top-1 h-4 w-4 rounded-full bg-on-primary transition-all ${
                  highDensity ? 'right-1' : 'left-1'
                }`}
              />
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  )
}

/* ═══════════════════════════════════════════════════
   SYSTEM STATUS TAB
   ═══════════════════════════════════════════════════ */

const SERVICES = [
  { endpoint: 'api.projectlens.ai/v1/inference', status: 'OPERATIONAL', latency: '124ms' },
  { endpoint: 'vector-db.us-east-1.aws', status: 'OPERATIONAL', latency: '42ms' },
  { endpoint: 'assets-ingestion-worker', status: 'DEGRADED', latency: '1.2s' },
]

function SystemStatusTab() {
  return (
    <div className="grid grid-cols-1 gap-lg md:grid-cols-3">
      {/* Left Column */}
      <motion.div variants={itemStagger} className="md:col-span-1">
        <h2 className="mb-xs font-headline-md text-on-surface">Infrastructure Health</h2>
        <p className="font-body-md text-sm text-on-surface-variant">
          Real-time metrics on service availability, latency, and API key security.
        </p>
      </motion.div>

      {/* Right Column */}
      <motion.div variants={itemStagger} className="flex flex-col gap-lg md:col-span-2">
        {/* Services Table */}
        <div className="glass-card overflow-hidden rounded-xl">
          <table className="w-full text-left font-body-md">
            <thead className="bg-surface-container-high">
              <tr>
                <th className="px-lg py-3 font-label-md text-[11px] uppercase tracking-wider text-outline">
                  Endpoint
                </th>
                <th className="px-lg py-3 font-label-md text-[11px] uppercase tracking-wider text-outline">
                  Status
                </th>
                <th className="px-lg py-3 font-label-md text-[11px] uppercase tracking-wider text-outline">
                  Latency
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-outline-variant/30">
              {SERVICES.map((svc) => (
                <tr key={svc.endpoint} className="transition-colors hover:bg-surface-container-low">
                  <td className="px-lg py-md font-body-md font-bold text-on-surface">{svc.endpoint}</td>
                  <td className="px-lg py-md">
                    <div className="flex items-center gap-2">
                      <span
                        className={`block h-2 w-2 rounded-full ${
                          svc.status === 'OPERATIONAL'
                            ? 'bg-emerald-500 shadow-[0_0_6px_rgba(34,197,94,0.6)]'
                            : 'bg-amber-500 shadow-[0_0_6px_rgba(245,158,11,0.6)]'
                        }`}
                      />
                      <span
                        className={`font-body-md ${
                          svc.status === 'OPERATIONAL' ? 'text-emerald-400' : 'text-amber-400'
                        }`}
                      >
                        {svc.status}
                      </span>
                    </div>
                  </td>
                  <td className="px-lg py-md font-code-sm text-on-surface-variant">{svc.latency}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* API Key Management */}
        <div className="glass-card flex flex-col gap-lg rounded-xl p-lg">
          <label className="font-label-md text-[11px] uppercase text-outline">API Key</label>
          <div className="flex items-center justify-between rounded-lg bg-surface-container-low p-md">
            <div className="flex items-center gap-md">
              <Icon className="text-primary" size="20px">
                key
              </Icon>
              <span className="font-code-sm text-on-surface-variant">sk_lens_live_****...3f9a</span>
            </div>
            <div className="flex items-center gap-md">
              <button className="flex h-8 w-8 items-center justify-center rounded-lg transition-colors hover:bg-surface-container-high">
                <Icon className="text-on-surface-variant" size="18px">
                  content_copy
                </Icon>
              </button>
              <button className="rounded-full border border-error px-lg py-1 font-body-md text-error transition-colors hover:bg-error/10">
                Revoke All
              </button>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  )
}
