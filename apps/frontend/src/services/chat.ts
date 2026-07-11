import type { ChatSession, ChatMessage } from '@/types'
import { NotImplementedError } from './base'

export const ChatService = {
  async listSessions(): Promise<ChatSession[]> {
    throw new NotImplementedError('ChatService', 'listSessions')
  },

  async getSession(_id: string): Promise<ChatSession> {
    throw new NotImplementedError('ChatService', 'getSession')
  },

  async createSession(_data: {
    title?: string
    reportIds?: string[]
    mode?: string
  }): Promise<ChatSession> {
    throw new NotImplementedError('ChatService', 'createSession')
  },

  async deleteSession(_id: string): Promise<void> {
    throw new NotImplementedError('ChatService', 'deleteSession')
  },

  async getMessages(_sessionId: string): Promise<ChatMessage[]> {
    throw new NotImplementedError('ChatService', 'getMessages')
  },

  async sendMessage(
    _sessionId: string,
    _content: string
  ): Promise<ChatMessage> {
    throw new NotImplementedError('ChatService', 'sendMessage')
  },

  async streamMessage(
    _sessionId: string,
    _content: string,
    _onChunk: (_chunk: string) => void
  ): Promise<ChatMessage> {
    throw new NotImplementedError('ChatService', 'streamMessage')
  },
}
