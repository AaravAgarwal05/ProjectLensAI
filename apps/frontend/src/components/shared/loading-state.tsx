'use client'

import { cn } from '@/lib/utils'
import { Spinner } from '@/components/ui/spinner'

interface LoadingStateProps {
  title?: string
  description?: string
  className?: string
}

export function LoadingState({
  title = 'Loading...',
  description,
  className,
}: LoadingStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center py-16 text-center',
        className
      )}
    >
      <Spinner size="lg" />
      <h3 className="mt-4 text-lg font-semibold text-surface-900">{title}</h3>
      {description && (
        <p className="mt-1 max-w-md text-sm text-surface-500">{description}</p>
      )}
    </div>
  )
}
