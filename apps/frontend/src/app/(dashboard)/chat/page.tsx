'use client'

import { useState, useRef, useEffect } from 'react'
import {
  MessageSquare,
  Send,
  Plus,
  Search,
  FileText,
} from 'lucide-react'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

interface Conversation {
  id: string
  title: string
  lastMessage: string
  timestamp: Date
  unread: boolean
}

const initialConversations: Conversation[] = [
  {
    id: '1',
    title: 'Q4 Financial Report',
    lastMessage: 'What were the key revenue drivers this quarter?',
    timestamp: new Date(Date.now() - 1000 * 60 * 15),
    unread: true,
  },
  {
    id: '2',
    title: 'Market Research 2024',
    lastMessage: 'Summarize the competitor analysis section',
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2),
    unread: false,
  },
  {
    id: '3',
    title: 'Contract Draft v3',
    lastMessage: 'Are there any unusual clauses in this contract?',
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 24),
    unread: false,
  },
  {
    id: '4',
    title: 'Competitor Analysis',
    lastMessage: 'Compare our pricing vs competitors',
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 48),
    unread: false,
  },
]

const sampleMessages: Record<string, Message[]> = {
  '1': [
    {
      id: 'm1',
      role: 'user',
      content: 'What were the key revenue drivers this quarter?',
      timestamp: new Date(Date.now() - 1000 * 60 * 15),
    },
    {
      id: 'm2',
      role: 'assistant',
      content:
        'Based on the Q4 Financial Report, the key revenue drivers were:\n\n1. **Product Line A** - 45% of total revenue, grew 12% QoQ\n2. **Enterprise Services** - 30% of revenue, up 8% from last quarter\n3. **International Markets** - Contributed 25%, with APAC showing strongest growth at 18%\n\nThe total revenue for Q4 was $12.4M, exceeding projections by 7%.',
      timestamp: new Date(Date.now() - 1000 * 60 * 14),
    },
    {
      id: 'm3',
      role: 'user',
      content: 'How does this compare to last year?',
      timestamp: new Date(Date.now() - 1000 * 60 * 10),
    },
    {
      id: 'm4',
      role: 'assistant',
      content:
        'Compared to Q4 last year, revenue increased by **23%** ($12.4M vs $10.1M). Key growth areas:\n\n- Product Line A grew from 38% to 45% of revenue mix\n- International revenue share increased from 18% to 25%\n- Customer acquisition cost decreased by 15%\n- Average deal size increased from $24K to $31K',
      timestamp: new Date(Date.now() - 1000 * 60 * 9),
    },
  ],
}

export default function ChatPage() {
  const [conversations] = useState<Conversation[]>(initialConversations)
  const [activeConvId, setActiveConvId] = useState<string | null>('1')
  const [messages, setMessages] = useState<Message[]>(
    sampleMessages['1'] || [],
  )
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isTyping])

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim()) return

    const userMsg: Message = {
      id: `m${Date.now()}`,
      role: 'user',
      content: input,
      timestamp: new Date(),
    }
    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setIsTyping(true)

    setTimeout(() => {
      const assistantMsg: Message = {
        id: `m${Date.now() + 1}`,
        role: 'assistant',
        content:
          'Thank you for your question. I\'ve analyzed the document and here\'s what I found. The document contains relevant information that addresses your query. Would you like me to dive deeper into any specific aspect?',
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, assistantMsg])
      setIsTyping(false)
    }, 1500)
  }

  const activeConversation = conversations.find(
    (c) => c.id === activeConvId,
  )

  return (
    <div className="flex h-[calc(100vh-8rem)] -mx-6 -mb-6 overflow-hidden">
      {/* Conversation List */}
      <div className="w-80 shrink-0 border-r border-surface-200 bg-white">
        <div className="flex items-center justify-between border-b border-surface-200 px-4 py-4">
          <h2 className="text-lg font-semibold text-surface-900">Chats</h2>
          <button className="rounded-lg p-2 text-surface-400 transition-colors hover:bg-surface-100 hover:text-surface-600">
            <Plus className="h-5 w-5" />
          </button>
        </div>

        <div className="border-b border-surface-200 px-4 py-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-surface-400" />
            <input
              type="text"
              placeholder="Search conversations..."
              className="input-field pl-9"
            />
          </div>
        </div>

        <div className="overflow-y-auto" style={{ height: 'calc(100% - 9rem)' }}>
          {conversations.map((conv) => (
            <button
              key={conv.id}
              onClick={() => setActiveConvId(conv.id)}
              className={`w-full border-b border-surface-100 px-4 py-4 text-left transition-colors hover:bg-surface-50 ${
                activeConvId === conv.id ? 'bg-primary-50' : ''
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-surface-100">
                    <MessageSquare className="h-4 w-4 text-surface-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-surface-900 truncate">
                      {conv.title}
                    </p>
                    <p className="mt-0.5 text-xs text-surface-500 truncate">
                      {conv.lastMessage}
                    </p>
                  </div>
                </div>
                <div className="flex flex-col items-end gap-1.5">
                  <span className="text-xs text-surface-400">
                    {conv.timestamp.toLocaleDateString()}
                  </span>
                  {conv.unread && (
                    <span className="h-2 w-2 rounded-full bg-primary-500" />
                  )}
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex flex-1 flex-col bg-white">
        {activeConversation ? (
          <>
            {/* Chat Header */}
            <div className="flex items-center gap-3 border-b border-surface-200 px-6 py-4">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary-50">
                <FileText className="h-4 w-4 text-primary-600" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-surface-900">
                  {activeConversation.title}
                </h3>
                <p className="text-xs text-surface-400">
                  Document chat &middot; Active
                </p>
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-6 py-6">
              <div className="mx-auto max-w-3xl space-y-6">
                {messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex ${
                      msg.role === 'user'
                        ? 'justify-end'
                        : 'justify-start'
                    }`}
                  >
                    <div
                      className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                        msg.role === 'user'
                          ? 'bg-primary-600 text-white'
                          : 'bg-surface-100 text-surface-900'
                      }`}
                    >
                      <p className="whitespace-pre-wrap text-sm leading-6">
                        {msg.content}
                      </p>
                      <p
                        className={`mt-1.5 text-right text-xs ${
                          msg.role === 'user'
                            ? 'text-primary-200'
                            : 'text-surface-400'
                        }`}
                      >
                        {msg.timestamp.toLocaleTimeString([], {
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </p>
                    </div>
                  </div>
                ))}

                {isTyping && (
                  <div className="flex justify-start">
                    <div className="rounded-2xl bg-surface-100 px-4 py-3">
                      <div className="flex items-center gap-1">
                        <span className="h-2 w-2 animate-bounce rounded-full bg-surface-400" />
                        <span
                          className="h-2 w-2 animate-bounce rounded-full bg-surface-400"
                          style={{ animationDelay: '0.1s' }}
                        />
                        <span
                          className="h-2 w-2 animate-bounce rounded-full bg-surface-400"
                          style={{ animationDelay: '0.2s' }}
                        />
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            </div>

            {/* Input Area */}
            <div className="border-t border-surface-200 px-6 py-4">
              <form
                onSubmit={handleSend}
                className="mx-auto flex max-w-3xl items-center gap-3"
              >
                <input
                  type="text"
                  placeholder="Ask a question about your document..."
                  className="input-field flex-1"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                />
                <button
                  type="submit"
                  disabled={!input.trim() || isTyping}
                  className="btn-primary rounded-lg p-3"
                >
                  <Send className="h-4 w-4" />
                </button>
              </form>
              <p className="mt-2 text-center text-xs text-surface-400">
                AI responses are generated based on document content. Verify
                important information.
              </p>
            </div>
          </>
        ) : (
          /* Empty state */
          <div className="flex flex-1 items-center justify-center">
            <div className="text-center">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-surface-100">
                <MessageSquare className="h-8 w-8 text-surface-400" />
              </div>
              <h3 className="mt-6 text-lg font-semibold text-surface-900">
                No conversation selected
              </h3>
              <p className="mt-2 text-sm text-surface-500">
                Choose a conversation from the sidebar or start a new one.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
