'use client'

import { cn } from '@/lib/utils'

interface TabsProps {
  tabs: { id: string; label: string; count?: number }[]
  activeTab: string
  onTabChange: (tab: string) => void
  className?: string
}

export function Tabs({
  tabs,
  activeTab,
  onTabChange,
  className,
}: TabsProps) {
  return (
    <div className={cn('flex gap-1 border-b border-surface-200', className)}>
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onTabChange(tab.id)}
          className={cn(
            'relative flex items-center gap-2 px-4 py-2.5 text-sm font-medium transition-colors',
            activeTab === tab.id
              ? 'text-primary-700'
              : 'text-surface-500 hover:text-surface-700'
          )}
        >
          {tab.label}
          {tab.count !== undefined && (
            <span
              className={cn(
                'inline-flex items-center justify-center rounded-full px-2 py-0.5 text-xs',
                activeTab === tab.id
                  ? 'bg-primary-100 text-primary-700'
                  : 'bg-surface-100 text-surface-500'
              )}
            >
              {tab.count}
            </span>
          )}
          {activeTab === tab.id && (
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-600" />
          )}
        </button>
      ))}
    </div>
  )
}
