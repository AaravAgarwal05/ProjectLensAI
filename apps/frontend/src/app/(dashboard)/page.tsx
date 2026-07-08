'use client'

import {
  FileText,
  MessageSquare,
  BarChart3,
  HardDrive,
  ArrowUpRight,
  Clock,
} from 'lucide-react'

const stats = [
  {
    label: 'Total Documents',
    value: '24',
    change: '+3 this week',
    icon: FileText,
    color: 'text-primary-600',
    bg: 'bg-primary-50',
  },
  {
    label: 'Active Chats',
    value: '8',
    change: '+2 today',
    icon: MessageSquare,
    color: 'text-accent-600',
    bg: 'bg-accent-50',
  },
  {
    label: 'Analyses Run',
    value: '156',
    change: '+12 this week',
    icon: BarChart3,
    color: 'text-primary-600',
    bg: 'bg-primary-50',
  },
  {
    label: 'Storage Used',
    value: '2.4 GB',
    change: 'of 10 GB',
    icon: HardDrive,
    color: 'text-surface-600',
    bg: 'bg-surface-100',
  },
]

const recentActivity = [
  {
    action: 'Uploaded',
    target: 'Q4 Financial Report.pdf',
    time: '2 minutes ago',
    type: 'document',
  },
  {
    action: 'Completed analysis on',
    target: 'Market Research 2024',
    time: '15 minutes ago',
    type: 'analysis',
  },
  {
    action: 'Chat with',
    target: 'Q4 Financial Report',
    time: '1 hour ago',
    type: 'chat',
  },
  {
    action: 'Shared',
    target: 'Competitor Analysis',
    time: '3 hours ago',
    type: 'document',
  },
  {
    action: 'Uploaded',
    target: 'Contract Draft v3.docx',
    time: '5 hours ago',
    type: 'document',
  },
]

const activityIcons: Record<string, typeof FileText> = {
  document: FileText,
  analysis: BarChart3,
  chat: MessageSquare,
}

export default function DashboardPage() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-surface-900">
          Welcome back, John
        </h1>
        <p className="mt-1 text-sm text-surface-500">
          Here&apos;s what&apos;s happening with your documents today.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <div key={stat.label} className="card">
            <div className="flex items-start justify-between">
              <div className={`rounded-lg ${stat.bg} p-2.5`}>
                <stat.icon className={`h-5 w-5 ${stat.color}`} />
              </div>
              <span className="inline-flex items-center gap-0.5 text-xs font-medium text-accent-600">
                <ArrowUpRight className="h-3 w-3" />
                {stat.change}
              </span>
            </div>
            <div className="mt-4">
              <p className="text-2xl font-bold text-surface-900">
                {stat.value}
              </p>
              <p className="mt-1 text-sm text-surface-500">{stat.label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Recent Activity */}
      <div className="card">
        <div className="mb-6 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Clock className="h-5 w-5 text-surface-500" />
            <h2 className="text-lg font-semibold text-surface-900">
              Recent Activity
            </h2>
          </div>
          <button className="text-sm font-medium text-primary-600 hover:text-primary-700">
            View all
          </button>
        </div>
        <div className="space-y-1">
          {recentActivity.map((item, index) => {
            const Icon = activityIcons[item.type] || FileText
            return (
              <div
                key={index}
                className="flex items-center gap-4 rounded-lg px-3 py-3 transition-colors hover:bg-surface-50"
              >
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-surface-100">
                  <Icon className="h-4 w-4 text-surface-600" />
                </div>
                <div className="flex-1">
                  <p className="text-sm text-surface-900">
                    <span className="font-medium">{item.action}</span>{' '}
                    {item.target}
                  </p>
                </div>
                <span className="text-xs text-surface-400">{item.time}</span>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
