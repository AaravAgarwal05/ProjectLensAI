import { afterEach, describe, expect, it, vi } from 'vitest'

import { ApiError, API_BASE } from '@/lib/api'
import { ChatService } from '@/services/chat'
import { jsonResponse, mockFetch } from '@/test/helpers'

afterEach(() => {
  vi.unstubAllGlobals()
})

const RAW_SESSION = {
  id: 's1',
  title: 'New Chat',
  report_ids: ['r1'],
  mode: 'single',
  message_count: 2,
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-02T00:00:00Z',
  archived: false,
}

const RAW_MESSAGE = {
  id: 'm1',
  role: 'assistant',
  content: 'Answer',
  citations: [
    {
      report_id: 'r1',
      report_title: 'Annual',
      page_number: 3,
      section_name: 'Intro',
      chunk_id: 'ch1',
      score: 0.9,
    },
  ],
  created_at: '2025-01-01T00:00:00Z',
}

describe('ChatService session operations', () => {
  it('listSessions maps report_ids → reportIds and count → messageCount', async () => {
    const fn = mockFetch()
    fn.mockResolvedValue(jsonResponse(200, [RAW_SESSION]))

    const sessions = await ChatService.listSessions({ includeArchived: true, limit: 10 })

    const [url] = fn.mock.calls[0] as [string]
    expect(url).toBe(`${API_BASE}/chat/conversations?include_archived=true&limit=10`)
    expect(sessions[0]).toMatchObject({
      id: 's1',
      title: 'New Chat',
      reportIds: ['r1'],
      mode: 'single',
      messageCount: 2,
      archived: false,
    })
  })

  it('createSession defaults title/reportIds/mode', async () => {
    const fn = mockFetch()
    fn.mockResolvedValue(jsonResponse(201, RAW_SESSION))

    await ChatService.createSession({})

    const [, init] = fn.mock.calls[0] as [string, RequestInit]
    expect(init.body).toBe(JSON.stringify({ title: 'New Chat', report_ids: [], mode: 'single' }))
  })

  it('createSession passes through provided values', async () => {
    const fn = mockFetch()
    fn.mockResolvedValue(jsonResponse(201, { ...RAW_SESSION, report_ids: ['r9'], mode: 'compare' }))

    const session = await ChatService.createSession({ reportIds: ['r9'], mode: 'compare' })

    const [, init] = fn.mock.calls[0] as [string, RequestInit]
    expect(init.body).toBe(JSON.stringify({ title: 'New Chat', report_ids: ['r9'], mode: 'compare' }))
    expect(session.reportIds).toEqual(['r9'])
  })

  it('updateSession maps camelCase back to snake_case', async () => {
    const fn = mockFetch()
    fn.mockResolvedValue(jsonResponse(200, RAW_SESSION))

    await ChatService.updateSession('s1', { title: 'Renamed', reportIds: ['r2'] })

    const [, init] = fn.mock.calls[0] as [string, RequestInit]
    expect(init.method).toBe('PATCH')
    expect(init.body).toBe(JSON.stringify({ title: 'Renamed', report_ids: ['r2'] }))
  })

  it('deleteSession and archiveSession hit the right routes', async () => {
    const fn = mockFetch()
    fn.mockResolvedValueOnce(jsonResponse(200, RAW_SESSION))
    fn.mockResolvedValueOnce(jsonResponse(200, RAW_SESSION))

    await ChatService.deleteSession('s1')
    expect(fn).toHaveBeenLastCalledWith(
      `${API_BASE}/chat/conversations/s1`,
      expect.objectContaining({ method: 'DELETE' })
    )

    await ChatService.archiveSession('s1')
    expect(fn).toHaveBeenLastCalledWith(
      `${API_BASE}/chat/conversations/s1/archive`,
      expect.objectContaining({ method: 'POST' })
    )
  })
})

describe('ChatService messages', () => {
  it('sendMessage builds the body and maps the reply', async () => {
    const fn = mockFetch()
    fn.mockResolvedValue(
      jsonResponse(200, { session_id: 's1', message: RAW_MESSAGE, citations: [] })
    )

    const msg = await ChatService.sendMessage('s1', 'hi', { reportIds: ['r1'], mode: 'single' })

    const [, init] = fn.mock.calls[0] as [string, RequestInit]
    expect(init.body).toBe(
      JSON.stringify({ message: 'hi', session_id: 's1', report_ids: ['r1'], mode: 'single' })
    )
    expect(msg).toMatchObject({
      id: 'm1',
      sessionId: 's1',
      role: 'assistant',
      content: 'Answer',
      citations: [
        {
          chunkId: 'ch1',
          sourceId: 'r1',
          sourceTitle: 'Annual',
          score: 0.9,
          text: 'Intro',
        },
      ],
    })
  })
})

describe('ChatService.streamMessage', () => {
  function sseResponse(payloads: string[], status = 200): Response {
    const encoder = new TextEncoder()
    const body = payloads.map((p) => `data: ${p}\n\n`).join('')
    return new Response(
      new ReadableStream({
        start(controller) {
          controller.enqueue(encoder.encode(body))
          controller.close()
        },
      }),
      { status }
    )
  }

  it('accumulates tokens and invokes onChunk per token', async () => {
    const fn = mockFetch()
    fn.mockResolvedValue(
      sseResponse([
        '{"type":"token","text":"Hello"}',
        '{"type":"token","text":" world"}',
        '{"type":"done","session_id":"s1"}',
      ])
    )

    const chunks: string[] = []
    const msg = await ChatService.streamMessage('s0', 'hi', (t) => chunks.push(t))

    const [url, init] = fn.mock.calls[0] as [string, RequestInit]
    expect(url).toBe(`${API_BASE}/chat/send/stream`)
    expect(init.method).toBe('POST')
    expect(init.headers).toEqual({ 'Content-Type': 'application/json' })

    expect(chunks).toEqual(['Hello', ' world'])
    expect(msg).toMatchObject({
      sessionId: 's1',
      role: 'assistant',
      content: 'Hello world',
      citations: undefined,
    })
    expect(msg.id.startsWith('stream-')).toBe(true)
    expect(new Date(msg.createdAt).toString()).not.toBe('Invalid Date')
  })

  it('uses the fallback session id when done omits it', async () => {
    const fn = mockFetch()
    fn.mockResolvedValue(sseResponse(['{"type":"done"}']))

    const msg = await ChatService.streamMessage('s0', 'hi', () => {})

    expect(msg.sessionId).toBe('s0')
    expect(msg.content).toBe('')
  })

  it('rejects with ApiError on a stream error event', async () => {
    const fn = mockFetch()
    fn.mockResolvedValue(sseResponse(['{"type":"error","message":"model overloaded"}']))

    const err = await ChatService.streamMessage('s0', 'hi', () => {}).catch((e) => e)

    expect(err).toBeInstanceOf(ApiError)
    expect(err.status).toBe(500)
    expect(err.message).toBe('model overloaded')
  })

  it('skips malformed JSON lines without aborting', async () => {
    const fn = mockFetch()
    fn.mockResolvedValue(
      sseResponse([
        'not-json',
        '{"type":"token","text":"ok"}',
        '{"type":"done"}',
      ])
    )

    const msg = await ChatService.streamMessage('s0', 'hi', () => {})

    expect(msg.content).toBe('ok')
  })

  it('rejects on a non-ok HTTP response', async () => {
    const fn = mockFetch()
    fn.mockResolvedValue(jsonResponse(500, { detail: 'server error' }, 'Internal Server Error'))

    const err = await ChatService.streamMessage('s0', 'hi', () => {}).catch((e) => e)

    expect(err).toBeInstanceOf(ApiError)
    expect(err.status).toBe(500)
    expect(err.message).toBe('server error')
  })
})
