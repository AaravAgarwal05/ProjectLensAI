/**
 * Settings service — reads/writes user processing preferences via API.
 */

import { apiRequest } from '@/lib/api'

// ─── Types ───────────────────────────────────────────────────────────────────

export interface ProcessingPreferences {
  chunking_strategy: string
  llm_provider: string
  retrieval_strategy: string
  embedding_provider: string
}

interface PreferencesResponse {
  preferences: ProcessingPreferences
}

// ─── Defaults (mirrored from backend) ────────────────────────────────────────

export const DEFAULT_PREFERENCES: ProcessingPreferences = {
  chunking_strategy: 'heading_aware',
  llm_provider: 'opencode_zen',
  retrieval_strategy: 'hybrid',
  embedding_provider: 'ollama',
}

// ─── Options + descriptions (mirrored from backend capabilities) ─────────────

export const CHUNKING_OPTIONS = [
  { value: 'heading_aware', label: 'Heading-aware', description: 'Preserves document section hierarchy — default' },
  { value: 'recursive', label: 'Recursive', description: 'Recursively splits long sections at paragraph boundaries' },
  { value: 'fixed', label: 'Fixed-size', description: 'Uniform fixed-size chunks, with overlap' },
]

export const LLM_OPTIONS = [
  { value: 'opencode_zen', label: 'OpenCode Zen', description: 'DeepSeek v4 Flash (free) — default' },
  { value: 'google', label: 'Google Gemini', description: 'Gemini 2.5 Flash — cloud LLM' },
  { value: 'ollama', label: 'Ollama', description: 'Local LLM — private, offline' },
]

export const RETRIEVAL_OPTIONS = [
  { value: 'hybrid', label: 'Hybrid', description: 'Vector + BM25 + reranking — default' },
  { value: 'dense', label: 'Dense', description: 'Vector similarity only — fastest' },
  { value: 'multi_query', label: 'Multi-query', description: 'Expands query into variants — broadest recall' },
]

export const EMBEDDING_OPTIONS = [
  { value: 'ollama', label: 'Ollama', description: 'nomic-embed-text via Ollama — default' },
  { value: 'sentence_transformer', label: 'Sentence Transformers', description: 'On-device embeddings — no external server' },
]

export const SettingsService = {
  /** Fetch the current user's processing preferences from the backend. */
  async getProcessingPreferences(): Promise<ProcessingPreferences> {
    try {
      const res = await apiRequest<PreferencesResponse>('/settings/processing-preferences')
      return res.preferences
    } catch {
      // Return defaults if the API isn't reachable (e.g. during development)
      return { ...DEFAULT_PREFERENCES }
    }
  },

  /** Update the current user's processing preferences on the backend. */
  async updateProcessingPreferences(
    prefs: Partial<ProcessingPreferences>
  ): Promise<ProcessingPreferences> {
    const res = await apiRequest<PreferencesResponse>('/settings/processing-preferences', {
      method: 'PUT',
      body: prefs,
    })
    return res.preferences
  },
}
