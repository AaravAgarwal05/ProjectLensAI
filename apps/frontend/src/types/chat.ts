export type ChatMode = 'single' | 'multi' | 'comparison'

export interface ChatSession {
  id: string
  title: string
  mode: ChatMode
  reportIds: string[]
  messageCount: number
  createdAt: string
  updatedAt: string
  archived: boolean
}

export interface ChatMessage {
  id: string
  sessionId: string
  role: 'user' | 'assistant'
  content: string
  citations?: Citation[]
  createdAt: string
}

export interface Citation {
  chunkId: string
  sourceId: string
  sourceTitle: string
  score: number
  text: string
}
