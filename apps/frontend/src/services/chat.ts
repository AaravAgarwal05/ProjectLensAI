import type { ChatSession, ChatMessage, Citation } from '@/types'
import { apiRequest } from '@/lib/api'

// ---------------------------------------------------------------------------
// Raw backend response types (snake_case)
// ---------------------------------------------------------------------------

interface SessionOut {
  id: string
  title: string
  report_ids: string[]
  mode: string
  message_count: number
  created_at: string
  updated_at: string
  archived: boolean
}

interface MessageOut {
  id: string
  role: string
  content: string
  citations: CitationRefOut[]
  created_at: string
}

interface CitationRefOut {
  report_id: string
  report_title: string
  page_number: number | null
  section_name: string
  chunk_id: string
  score: number
}

interface SendMessageResponse {
  session_id: string
  message: MessageOut
  citations: CitationRefOut[]
}

// ---------------------------------------------------------------------------
// Mappers
// ---------------------------------------------------------------------------

function mapSession(s: SessionOut): ChatSession {
  return {
    id: s.id,
    title: s.title,
    reportIds: s.report_ids,
    mode: s.mode as ChatSession['mode'],
    messageCount: s.message_count,
    createdAt: s.created_at,
    updatedAt: s.updated_at,
    archived: s.archived,
  }
}

function mapMessage(m: MessageOut, sessionId: string): ChatMessage {
  const citations: Citation[] = (m.citations ?? []).map((c) => ({
    chunkId: c.chunk_id,
    sourceId: c.report_id,
    sourceTitle: c.report_title,
    score: c.score,
    text: c.section_name || '',
  }))

  return {
    id: m.id,
    sessionId,
    role: m.role as 'user' | 'assistant',
    content: m.content,
    citations: citations.length > 0 ? citations : undefined,
    createdAt: m.created_at,
  }
}

// ---------------------------------------------------------------------------
// Service
// ---------------------------------------------------------------------------

export const ChatService = {
  /** List chat sessions with optional filtering and pagination. */
  async listSessions(
    params?: {
      includeArchived?: boolean
      limit?: number
      offset?: number
    }
  ): Promise<ChatSession[]> {
    const query = new URLSearchParams()
    if (params?.includeArchived) query.set('include_archived', 'true')
    if (params?.limit) query.set('limit', String(params.limit))
    if (params?.offset) query.set('offset', String(params.offset))
    const qs = query.toString()
    const data = await apiRequest<SessionOut[]>(
      `/chat/conversations${qs ? '?' + qs : ''}`
    )
    return data.map(mapSession)
  },

  /** Get a single chat session by ID. */
  async getSession(id: string): Promise<ChatSession> {
    const data = await apiRequest<SessionOut>(`/chat/conversations/${id}`)
    return mapSession(data)
  },

  /** Create a new chat session. */
  async createSession(data: {
    title?: string
    reportIds?: string[]
    mode?: string
  }): Promise<ChatSession> {
    const body = {
      title: data.title ?? 'New Chat',
      report_ids: data.reportIds ?? [],
      mode: data.mode ?? 'single',
    }
    const result = await apiRequest<SessionOut>('/chat/conversations', {
      method: 'POST',
      body,
    })
    return mapSession(result)
  },

  /** Update a chat session (title, mode, reportIds). */
  async updateSession(
    id: string,
    data: { title?: string; mode?: string; reportIds?: string[] }
  ): Promise<ChatSession> {
    const body: Record<string, unknown> = {}
    if (data.title !== undefined) body.title = data.title
    if (data.mode !== undefined) body.mode = data.mode
    if (data.reportIds !== undefined) body.report_ids = data.reportIds
    const result = await apiRequest<SessionOut>(
      `/chat/conversations/${id}`,
      { method: 'PATCH', body }
    )
    return mapSession(result)
  },

  /** Delete a chat session and all its messages. */
  async deleteSession(id: string): Promise<void> {
    await apiRequest(`/chat/conversations/${id}`, { method: 'DELETE' })
  },

  /** Archive a chat session. */
  async archiveSession(id: string): Promise<ChatSession> {
    const result = await apiRequest<SessionOut>(
      `/chat/conversations/${id}/archive`,
      { method: 'POST' }
    )
    return mapSession(result)
  },

  /** Restore an archived chat session. */
  async restoreSession(id: string): Promise<ChatSession> {
    const result = await apiRequest<SessionOut>(
      `/chat/conversations/${id}/restore`,
      { method: 'POST' }
    )
    return mapSession(result)
  },

  /** List messages in a session. */
  async getMessages(
    sessionId: string,
    params?: { limit?: number; offset?: number }
  ): Promise<ChatMessage[]> {
    const query = new URLSearchParams()
    if (params?.limit) query.set('limit', String(params.limit))
    if (params?.offset) query.set('offset', String(params.offset))
    const qs = query.toString()
    const data = await apiRequest<MessageOut[]>(
      `/chat/conversations/${sessionId}/messages${qs ? '?' + qs : ''}`
    )
    return data.map((m) => mapMessage(m, sessionId))
  },

  /** Send a message and get an AI response. */
  async sendMessage(
    sessionId: string,
    content: string,
    extra?: { reportIds?: string[]; mode?: string }
  ): Promise<ChatMessage> {
    const body: Record<string, unknown> = {
      message: content,
      session_id: sessionId,
    }
    if (extra?.reportIds) body.report_ids = extra.reportIds
    if (extra?.mode) body.mode = extra.mode
    const result = await apiRequest<SendMessageResponse>('/chat/send', {
      method: 'POST',
      body,
    })
    return mapMessage(result.message, result.session_id)
  },

  /** Delete a single message. */
  async deleteMessage(sessionId: string, messageId: string): Promise<void> {
    await apiRequest(
      `/chat/conversations/${sessionId}/messages/${messageId}`,
      { method: 'DELETE' }
    )
  },

  /**
   * Stream a message chunk by chunk.
   * Backend does not support streaming yet — delivers full response as one chunk.
   */
  async streamMessage(
    sessionId: string,
    content: string,
    onChunk: (_chunk: string) => void
  ): Promise<ChatMessage> {
    const msg = await ChatService.sendMessage(sessionId, content)
    onChunk(msg.content)
    return msg
  },
}
