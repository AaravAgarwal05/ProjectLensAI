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
  llm_provider: 'ollama',
  retrieval_strategy: 'hybrid',
  embedding_provider: 'ollama',
}

// ─── Human-friendly labels ───────────────────────────────────────────────────

export const CHUNKING_OPTIONS = [
  { value: 'fixed', label: 'Standard', description: 'Fixed-size chunks — fast, uniform' },
  { value: 'heading_aware', label: 'Precise', description: 'Section-aware — respects document structure' },
  { value: 'recursive', label: 'Deep', description: 'Recursive splitting — detailed, context-aware' },
]

export const LLM_OPTIONS = [
  { value: 'ollama', label: 'Ollama', description: 'Local LLM — fast, private' },
  { value: 'claude', label: 'Claude', description: 'Anthropic Claude — smart, nuanced' },
  { value: 'gpt', label: 'GPT', description: 'OpenAI GPT — powerful, versatile' },
]

export const RETRIEVAL_OPTIONS = [
  { value: 'dense', label: 'Fast', description: 'Dense vector search — quick results' },
  { value: 'hybrid', label: 'Balanced', description: 'Hybrid search — good accuracy & speed' },
  { value: 'multi_query', label: 'Deep', description: 'Multi-query — thorough, best accuracy' },
]

export const EMBEDDING_OPTIONS = [
  { value: 'sentence_transformer', label: 'Local', description: 'On-device embeddings — private, no API key needed' },
  { value: 'ollama', label: 'Cloud', description: 'Remote embeddings — via Ollama server' },
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
