import { create } from 'zustand'
import type { ChatSession, ChatMessage } from '@/types'

interface ChatState {
  sessions: ChatSession[]
  activeSession: ChatSession | null
  messages: ChatMessage[]
  isLoadingSessions: boolean
  isLoadingMessages: boolean
  setSessions: (sessions: ChatSession[]) => void
  setActiveSession: (session: ChatSession | null) => void
  setMessages: (messages: ChatMessage[]) => void
  addMessage: (message: ChatMessage) => void
  setLoadingSessions: (loading: boolean) => void
  setLoadingMessages: (loading: boolean) => void
}

export const useChatStore = create<ChatState>((set) => ({
  sessions: [],
  activeSession: null,
  messages: [],
  isLoadingSessions: false,
  isLoadingMessages: false,
  setSessions: (sessions) => set({ sessions }),
  setActiveSession: (activeSession) => set({ activeSession }),
  setMessages: (messages) => set({ messages }),
  addMessage: (message) => set((s) => ({ messages: [...s.messages, message] })),
  setLoadingSessions: (isLoadingSessions) => set({ isLoadingSessions }),
  setLoadingMessages: (isLoadingMessages) => set({ isLoadingMessages }),
}))
