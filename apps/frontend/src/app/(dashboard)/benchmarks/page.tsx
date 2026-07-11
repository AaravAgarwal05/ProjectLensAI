'use client'

import { PageHeader } from '@/components/shared/page-header'
import { PageContainer } from '@/components/shared/page-container'
import { EmptyState } from '@/components/shared/empty-state'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { BarChart3, Play, RefreshCw } from 'lucide-react'

const placeholderBenchmarks = [
  { id: '1', name: 'LLM Response Time', status: 'completed', avgLatency: '1.2s', requests: 100, lastRun: '1 hour ago' },
  { id: '2', name: 'Embedding Throughput', status: 'completed', avgLatency: '0.3s', requests: 500, lastRun: '2 hours ago' },
  { id: '3', name: 'Retrieval Accuracy', status: 'running', avgLatency: '-', requests: '-', lastRun: 'Running now' },
]

const statusVariant = {
  completed: 'accent' as const,
  running: 'primary' as const,
  pending: 'default' as const,
  failed: 'danger' as const,
}

export default function BenchmarksPage() {
  const benchmarks = placeholderBenchmarks

  return (
    <PageContainer>
      <PageHeader
        title="Benchmarks"
        description="Performance and accuracy metrics for AI components"
        breadcrumbs={[{ label: 'Benchmarks' }]}
        icon={BarChart3}
        actions={
          <Button>
            <Play className="h-4 w-4" />
            Run All
          </Button>
        }
      />

      {benchmarks.length === 0 ? (
        <EmptyState
          title="No benchmarks yet"
          description="Run a benchmark to measure AI component performance."
          icon={BarChart3}
          action={<Button><Play className="h-4 w-4" />Run Benchmarks</Button>}
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {benchmarks.map((bm) => (
            <div
              key={bm.id}
              className="rounded-xl border border-surface-200 bg-white p-5 shadow-sm transition-colors hover:border-primary-200"
            >
              <div className="mb-3 flex items-center justify-between">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary-50">
                  <BarChart3 className="h-4 w-4 text-primary-600" />
                </div>
                <Badge
                  variant={statusVariant[bm.status as keyof typeof statusVariant]}
                >
                  {bm.status}
                </Badge>
              </div>
              <h3 className="text-sm font-semibold text-surface-900">
                {bm.name}
              </h3>
              <div className="mt-3 space-y-1.5 text-sm">
                <div className="flex justify-between">
                  <span className="text-surface-500">Avg Latency</span>
                  <span className="font-medium text-surface-700">{bm.avgLatency}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-surface-500">Requests</span>
                  <span className="font-medium text-surface-700">{bm.requests}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-surface-500">Last Run</span>
                  <span className="font-medium text-surface-700">{bm.lastRun}</span>
                </div>
              </div>
              <button className="mt-4 flex w-full items-center justify-center gap-1.5 rounded-lg border border-surface-200 px-3 py-2 text-xs font-medium text-surface-600 transition-colors hover:bg-surface-50">
                <RefreshCw className="h-3.5 w-3.5" />
                Run Again
              </button>
            </div>
          ))}
        </div>
      )}
    </PageContainer>
  )
}
