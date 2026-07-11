'use client'

import { cn } from '@/lib/utils'
import { Spinner } from '@/components/ui/spinner'
import { type LucideIcon } from 'lucide-react'

interface StatCardProps {
  title: string
  value: string | number
  description?: string
  icon?: LucideIcon
  trend?: { value: number; isPositive: boolean }
  isLoading?: boolean
  className?: string
}

export function StatCard({
  title,
  value,
  description,
  icon: Icon,
  trend,
  isLoading,
  className,
}: StatCardProps) {
  return (
    <div
      className={cn(
        'rounded-xl border border-surface-200 bg-white p-5 shadow-sm transition-shadow hover:shadow-md',
        className
      )}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-surface-500">{title}</p>
          {isLoading ? (
            <div className="mt-2">
              <Spinner size="sm" />
            </div>
          ) : (
            <>
              <p className="mt-1 text-2xl font-bold text-surface-900">
                {value}
              </p>
              {trend && (
                <p
                  className={cn(
                    'mt-1 text-xs font-medium',
                    trend.isPositive ? 'text-accent-600' : 'text-red-500'
                  )}
                >
                  {trend.isPositive ? '↑' : '↓'} {Math.abs(trend.value)}%
                  {description ? ` ${description}` : ''}
                </p>
              )}
              {!trend && description && (
                <p className="mt-1 text-xs text-surface-400">{description}</p>
              )}
            </>
          )}
        </div>
        {Icon && (
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary-50">
            <Icon className="h-5 w-5 text-primary-600" />
          </div>
        )}
      </div>
    </div>
  )
}
