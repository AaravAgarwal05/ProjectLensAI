import type {
  Report,
  Collection,
  ChatSession,
  ChatMessage,
} from '@/types'

/** Generate placeholder reports for UI scaffolding. */
export function placeholderReports(): Report[] {
  return [
    {
      id: '1',
      title: 'Q4 Financial Analysis Report',
      description: 'Comprehensive analysis of Q4 financial performance across all departments.',
      department: 'Finance',
      author: 'Sarah Chen',
      tags: ['finance', 'Q4', 'quarterly'],
      visibility: 'private',
      year: 2024,
      status: 'ready',
      fileSize: 2457600,
      mimeType: 'application/pdf',
      chunkCount: 42,
      createdAt: '2024-12-15T10:30:00Z',
      updatedAt: '2024-12-15T14:00:00Z',
    },
    {
      id: '2',
      title: 'Q3 Engineering Review',
      description: 'Engineering team performance and project delivery for Q3.',
      department: 'Engineering',
      author: 'Mike Torres',
      tags: ['engineering', 'Q3', 'sprint'],
      visibility: 'team',
      year: 2024,
      status: 'ready',
      fileSize: 1835008,
      mimeType: 'application/pdf',
      chunkCount: 28,
      createdAt: '2024-10-01T08:00:00Z',
      updatedAt: '2024-10-02T12:00:00Z',
    },
    {
      id: '3',
      title: 'Market Research 2024',
      description: 'Annual market research report with competitive analysis.',
      department: 'Strategy',
      author: 'Anna Williams',
      tags: ['market-research', 'strategy', 'annual'],
      visibility: 'public',
      year: 2024,
      status: 'processing',
      fileSize: 5242880,
      mimeType: 'application/pdf',
      chunkCount: 0,
      createdAt: '2025-01-20T09:15:00Z',
      updatedAt: '2025-01-20T09:15:00Z',
    },
    {
      id: '4',
      title: 'Security Audit Report',
      description: 'Internal security audit findings and recommendations.',
      department: 'Security',
      author: 'Alex Rivera',
      tags: ['security', 'audit', 'compliance'],
      visibility: 'private',
      year: 2024,
      status: 'error',
      fileSize: 1048576,
      mimeType: 'application/pdf',
      chunkCount: 0,
      createdAt: '2025-01-18T16:00:00Z',
      updatedAt: '2025-01-18T16:30:00Z',
    },
    {
      id: '5',
      title: 'Product Roadmap 2025',
      description: 'Strategic product roadmap and feature planning for 2025.',
      department: 'Product',
      author: 'Jordan Lee',
      tags: ['product', 'roadmap', 'strategic'],
      visibility: 'private',
      year: 2025,
      status: 'ready',
      fileSize: 3072000,
      mimeType: 'application/pdf',
      chunkCount: 35,
      createdAt: '2025-01-10T11:00:00Z',
      updatedAt: '2025-01-12T09:00:00Z',
    },
  ]
}

/** Generate placeholder collections for UI scaffolding. */
export function placeholderCollections(): Collection[] {
  return [
    { id: '1', name: 'Financial Reports', description: 'All quarterly and annual financial reports.', reportCount: 8, createdAt: '2024-06-01T00:00:00Z', updatedAt: '2025-01-15T00:00:00Z' },
    { id: '2', name: 'Engineering Docs', description: 'Technical documentation and specs.', reportCount: 15, createdAt: '2024-07-01T00:00:00Z', updatedAt: '2025-01-10T00:00:00Z' },
    { id: '3', name: 'Security Audits', description: 'Security and compliance audit reports.', reportCount: 4, createdAt: '2024-08-15T00:00:00Z', updatedAt: '2024-12-20T00:00:00Z' },
    { id: '4', name: 'Market Research', description: 'Market research and competitive analysis.', reportCount: 12, createdAt: '2024-09-01T00:00:00Z', updatedAt: '2025-01-05T00:00:00Z' },
  ]
}

/** Generate placeholder chat sessions for UI scaffolding. */
export function placeholderChatSessions(): ChatSession[] {
  return [
    { id: '1', title: 'Q4 Financial Analysis', mode: 'single', reportIds: ['1'], messageCount: 12, createdAt: '2025-01-15T10:00:00Z', updatedAt: '2025-01-15T10:30:00Z', archived: false },
    { id: '2', title: 'Engineering vs Finance Comparison', mode: 'comparison', reportIds: ['1', '2'], messageCount: 8, createdAt: '2025-01-14T14:00:00Z', updatedAt: '2025-01-14T14:20:00Z', archived: false },
    { id: '3', title: 'Market Research Summary', mode: 'single', reportIds: ['3'], messageCount: 5, createdAt: '2025-01-13T09:00:00Z', updatedAt: '2025-01-13T09:15:00Z', archived: false },
    { id: '4', title: 'Multi-Report Strategy Analysis', mode: 'multi', reportIds: ['1', '3', '5'], messageCount: 22, createdAt: '2025-01-12T11:00:00Z', updatedAt: '2025-01-12T12:00:00Z', archived: false },
  ]
}

/** Generate placeholder chat messages for UI scaffolding. */
export function placeholderChatMessages(): ChatMessage[] {
  return [
    { id: 'm1', sessionId: '1', role: 'user', content: 'What were the key financial highlights for Q4?', createdAt: '2025-01-15T10:00:00Z' },
    { id: 'm2', sessionId: '1', role: 'assistant', content: 'Based on the Q4 Financial Analysis Report, the key highlights include:\n\n1. **Revenue Growth**: 15% increase quarter-over-quarter, reaching $12.4M\n2. **Cost Reduction**: Operating expenses decreased by 8% due to automation initiatives\n3. **Profit Margin**: Net profit margin improved from 18% to 22%\n4. **Cash Flow**: Free cash flow of $3.1M, up 25% from Q3\n\nThe Engineering department showed the strongest performance with a 30% increase in productivity metrics.', citations: [
      { chunkId: 'c1', sourceId: '1', sourceTitle: 'Q4 Financial Analysis Report', score: 0.95, text: 'Revenue grew 15% QoQ to $12.4M' },
      { chunkId: 'c2', sourceId: '1', sourceTitle: 'Q4 Financial Analysis Report', score: 0.92, text: 'Operating expenses decreased 8%' },
    ], createdAt: '2025-01-15T10:00:30Z' },
    { id: 'm3', sessionId: '1', role: 'user', content: 'Which department had the best performance?', createdAt: '2025-01-15T10:05:00Z' },
    { id: 'm4', sessionId: '1', role: 'assistant', content: 'Engineering had the strongest performance in Q4, with:\n\n- **30% increase in productivity metrics**\n- On-time delivery of 94% of milestones\n- 15% reduction in bug reports\n- Successful launch of 3 major features\n\nFinance also performed well, exceeding revenue targets by 8%.', citations: [
      { chunkId: 'c3', sourceId: '1', sourceTitle: 'Q4 Financial Analysis Report', score: 0.88, text: 'Engineering productivity increased 30%' },
    ], createdAt: '2025-01-15T10:05:30Z' },
  ]
}
