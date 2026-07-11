'use client'

import { cn } from '@/lib/utils'

interface SectionCardProps {
  title: string
  description?: string
  children: React.ReactNode
  action?: React.ReactNode
  className?: string
}

export function SectionCard({
  title,
  description,
  children,
  action,
  className,
}: SectionCardProps) {
  return (
    <div
      className={cn(
        'rounded-xl border border-surface-200 bg-white shadow-sm',
        className
      )}
    >
      <div className="flex items-center justify-between border-b border-surface-100 px-6 py-4">
        <div>
          <h3 className="text-base font-semibold text-surface-900">{title}</h3>
          {description && (
            <p className="mt-0.5 text-sm text-surface-500">{description}</p>
          )}
        </div>
        {action && <div className="shrink-0">{action}</div>}
      </div>
      <div className="px-6 py-4">{children}</div>
    </div>
  )
}
