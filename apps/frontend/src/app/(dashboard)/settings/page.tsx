'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import { motion } from 'framer-motion'
import { DashboardLayout } from '@/components/layout/dashboard-layout'
import { Icon } from '@/components/shared/icon'
import {
  SettingsService,
  CHUNKING_OPTIONS,
  LLM_OPTIONS,
  RETRIEVAL_OPTIONS,
  EMBEDDING_OPTIONS,
  DEFAULT_PREFERENCES,
  type ProcessingPreferences,
} from '@/services/settings'

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
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [hasChanges, setHasChanges] = useState(false)
  const [origPrefs, setOrigPrefs] = useState<ProcessingPreferences>(DEFAULT_PREFERENCES)
  const [chunkingStrategy, setChunkingStrategy] = useState(DEFAULT_PREFERENCES.chunking_strategy)
  const [llmProvider, setLlmProvider] = useState(DEFAULT_PREFERENCES.llm_provider)
  const [retrievalStrategy, setRetrievalStrategy] = useState(DEFAULT_PREFERENCES.retrieval_strategy)
  const [embeddingProvider, setEmbeddingProvider] = useState(DEFAULT_PREFERENCES.embedding_provider)

  // Load preferences from backend on mount
  useEffect(() => {
    SettingsService.getProcessingPreferences()
      .then((prefs) => {
        setOrigPrefs(prefs)
        setChunkingStrategy(prefs.chunking_strategy)
        setLlmProvider(prefs.llm_provider)
        setRetrievalStrategy(prefs.retrieval_strategy)
        setEmbeddingProvider(prefs.embedding_provider)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  // Detect changes against original
  useEffect(() => {
    if (loading) return
    const changed =
      chunkingStrategy !== origPrefs.chunking_strategy ||
      llmProvider !== origPrefs.llm_provider ||
      retrievalStrategy !== origPrefs.retrieval_strategy ||
      embeddingProvider !== origPrefs.embedding_provider
    setHasChanges(changed)
  }, [chunkingStrategy, llmProvider, retrievalStrategy, embeddingProvider, origPrefs, loading])

  const handleSave = useCallback(async () => {
    setSaving(true)
    try {
      const updated = await SettingsService.updateProcessingPreferences({
        chunking_strategy: chunkingStrategy,
        llm_provider: llmProvider,
        retrieval_strategy: retrievalStrategy,
        embedding_provider: embeddingProvider,
      })
      setOrigPrefs(updated)
      setHasChanges(false)
    } catch {
      // error logged by apiRequest
    } finally {
      setSaving(false)
    }
  }, [chunkingStrategy, llmProvider, retrievalStrategy, embeddingProvider])

  const handleDiscard = useCallback(() => {
    setChunkingStrategy(origPrefs.chunking_strategy)
    setLlmProvider(origPrefs.llm_provider)
    setRetrievalStrategy(origPrefs.retrieval_strategy)
    setEmbeddingProvider(origPrefs.embedding_provider)
    setHasChanges(false)
  }, [origPrefs])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-32">
        <span className="inline-block h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 gap-lg md:grid-cols-3">
      {/* Left Column */}
      <motion.div variants={itemStagger} className="md:col-span-1">
        <h2 className="mb-xs font-headline-md text-on-surface">Processing Preferences</h2>
        <p className="font-body-md text-sm text-on-surface-variant">
          Choose how reports are chunked, embedded, and analyzed. These preferences are used when
          processing your uploaded documents.
        </p>
      </motion.div>

      {/* Right Column */}
      <motion.div variants={itemStagger} className="md:col-span-2">
        <div className="ai-glow glass-card flex flex-col gap-lg rounded-xl p-lg">
          {/* Chunking Strategy */}
          <div className="flex flex-col gap-sm">
            <div className="flex items-center gap-2">
              <Icon className="text-primary" size="18px">
                dashboard
              </Icon>
              <label className="font-label-md text-primary">Chunking Strategy</label>
            </div>
            <p className="font-body-md text-sm text-on-surface-variant mb-sm">
              Controls how documents are split into pieces for analysis.
            </p>
            <div className="grid grid-cols-3 gap-sm">
              {CHUNKING_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setChunkingStrategy(opt.value)}
                  className={`flex flex-col items-center gap-1 rounded-lg border px-md py-sm font-body-md transition-colors ${
                    chunkingStrategy === opt.value
                      ? 'border-primary bg-primary-container/10 text-primary'
                      : 'border-outline-variant text-on-surface-variant hover:text-on-surface'
                  }`}
                >
                  <Icon size="18px" fill={chunkingStrategy === opt.value}>
                    check_circle
                  </Icon>
                  <span className="font-bold">{opt.label}</span>
                  <span className="text-[11px] text-on-surface-variant">{opt.description}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Divider */}
          <div className="border-t border-outline-variant/30" />

          {/* LLM Provider */}
          <div className="flex flex-col gap-sm">
            <div className="flex items-center gap-2">
              <Icon className="text-primary" size="18px">
                auto_awesome
              </Icon>
              <label className="font-label-md text-primary">LLM Provider</label>
            </div>
            <p className="font-body-md text-sm text-on-surface-variant mb-sm">
              Select which language model powers analysis and chat responses.
            </p>
            <div className="grid grid-cols-3 gap-sm">
              {LLM_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setLlmProvider(opt.value)}
                  className={`flex flex-col items-center gap-1 rounded-lg border px-md py-sm font-body-md transition-colors ${
                    llmProvider === opt.value
                      ? 'border-primary bg-primary-container/10 text-primary'
                      : 'border-outline-variant text-on-surface-variant hover:text-on-surface'
                  }`}
                >
                  <Icon size="18px" fill={llmProvider === opt.value}>
                    check_circle
                  </Icon>
                  <span className="font-bold">{opt.label}</span>
                  <span className="text-[11px] text-on-surface-variant">{opt.description}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Divider */}
          <div className="border-t border-outline-variant/30" />

          {/* Retrieval Strategy */}
          <div className="flex flex-col gap-sm">
            <div className="flex items-center gap-2">
              <Icon className="text-primary" size="18px">
                search
              </Icon>
              <label className="font-label-md text-primary">Retrieval Strategy</label>
            </div>
            <p className="font-body-md text-sm text-on-surface-variant mb-sm">
              Determines how the system searches for relevant information.
            </p>
            <div className="grid grid-cols-3 gap-sm">
              {RETRIEVAL_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setRetrievalStrategy(opt.value)}
                  className={`flex flex-col items-center gap-1 rounded-lg border px-md py-sm font-body-md transition-colors ${
                    retrievalStrategy === opt.value
                      ? 'border-primary bg-primary-container/10 text-primary'
                      : 'border-outline-variant text-on-surface-variant hover:text-on-surface'
                  }`}
                >
                  <Icon size="18px" fill={retrievalStrategy === opt.value}>
                    check_circle
                  </Icon>
                  <span className="font-bold">{opt.label}</span>
                  <span className="text-[11px] text-on-surface-variant">{opt.description}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Divider */}
          <div className="border-t border-outline-variant/30" />

          {/* Embedding Provider */}
          <div className="flex flex-col gap-sm">
            <div className="flex items-center gap-2">
              <Icon className="text-primary" size="18px">
                texture
              </Icon>
              <label className="font-label-md text-primary">Embedding Provider</label>
            </div>
            <p className="font-body-md text-sm text-on-surface-variant mb-sm">
              Controls how document text is converted to vector embeddings.
            </p>
            <div className="grid grid-cols-2 gap-sm">
              {EMBEDDING_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setEmbeddingProvider(opt.value)}
                  className={`flex flex-col items-center gap-1 rounded-lg border px-md py-sm font-body-md transition-colors ${
                    embeddingProvider === opt.value
                      ? 'border-primary bg-primary-container/10 text-primary'
                      : 'border-outline-variant text-on-surface-variant hover:text-on-surface'
                  }`}
                >
                  <Icon size="18px" fill={embeddingProvider === opt.value}>
                    check_circle
                  </Icon>
                  <span className="font-bold">{opt.label}</span>
                  <span className="text-[11px] text-on-surface-variant">{opt.description}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Save / Discard inline */}
        {hasChanges && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-lg flex items-center justify-end gap-sm"
          >
            <button
              onClick={handleDiscard}
              className="rounded-lg border border-outline-variant px-lg py-sm font-body-md text-on-surface-variant transition-colors hover:text-on-surface"
            >
              Discard
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="rounded-lg bg-primary px-lg py-sm font-body-md font-bold text-on-primary transition-opacity hover:opacity-90 disabled:opacity-50"
            >
              {saving ? 'Saving…' : 'Save Changes'}
            </button>
          </motion.div>
        )}
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
