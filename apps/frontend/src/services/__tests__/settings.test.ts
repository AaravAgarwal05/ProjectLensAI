import { afterEach, describe, expect, it, vi } from 'vitest'

import { API_BASE } from '@/lib/api'
import {
  CHUNKING_OPTIONS,
  DEFAULT_PREFERENCES,
  EMBEDDING_OPTIONS,
  LLM_OPTIONS,
  RETRIEVAL_OPTIONS,
  SettingsService,
} from '@/services/settings'
import { jsonResponse, mockFetch } from '@/test/helpers'

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('SettingsService.getProcessingPreferences', () => {
  it('returns preferences from the API', async () => {
    const fn = mockFetch()
    fn.mockResolvedValue(
      jsonResponse(200, {
        preferences: {
          chunking_strategy: 'recursive',
          llm_provider: 'google',
          retrieval_strategy: 'dense',
          embedding_provider: 'ollama',
        },
      })
    )

    const prefs = await SettingsService.getProcessingPreferences()

    expect(fn).toHaveBeenCalledWith(
      `${API_BASE}/settings/processing-preferences`,
      expect.any(Object)
    )
    expect(prefs).toEqual({
      chunking_strategy: 'recursive',
      llm_provider: 'google',
      retrieval_strategy: 'dense',
      embedding_provider: 'ollama',
    })
  })

  it('falls back to defaults when the API is unreachable', async () => {
    const fn = mockFetch()
    fn.mockResolvedValue(jsonResponse(500, { detail: 'boom' }, 'Internal Server Error'))

    const prefs = await SettingsService.getProcessingPreferences()

    expect(prefs).toEqual(DEFAULT_PREFERENCES)
    expect(prefs).not.toBe(DEFAULT_PREFERENCES) // fresh copy
  })
})

describe('SettingsService.updateProcessingPreferences', () => {
  it('PUTs the partial prefs', async () => {
    const fn = mockFetch()
    fn.mockResolvedValue(
      jsonResponse(200, { preferences: { ...DEFAULT_PREFERENCES, llm_provider: 'ollama' } })
    )

    const result = await SettingsService.updateProcessingPreferences({ llm_provider: 'ollama' })

    const [, init] = fn.mock.calls[0] as [string, RequestInit]
    expect(init.method).toBe('PUT')
    expect(init.body).toBe(JSON.stringify({ llm_provider: 'ollama' }))
    expect(result.llm_provider).toBe('ollama')
  })
})

describe('provider catalogs', () => {
  it('exposes the expected default first', () => {
    expect(CHUNKING_OPTIONS[0]?.value).toBe('heading_aware')
    expect(RETRIEVAL_OPTIONS[0]?.value).toBe('hybrid')
    expect(LLM_OPTIONS[0]?.value).toBe('opencode_zen')
    expect(EMBEDDING_OPTIONS[0]?.value).toBe('gemini')
  })
})
