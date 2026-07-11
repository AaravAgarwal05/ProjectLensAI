'use client'

import { PageHeader } from '@/components/shared/page-header'
import { PageContainer } from '@/components/shared/page-container'
import { EmptyState } from '@/components/shared/empty-state'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Workflow, Plus, Play, Settings } from 'lucide-react'

const placeholderWorkflows = [
  { id: '1', name: 'Document Analysis Pipeline', status: 'active', steps: 4, lastRun: '2 hours ago' },
  { id: '2', name: 'Daily Report Processing', status: 'active', steps: 3, lastRun: '1 day ago' },
  { id: '3', name: 'Monthly Compliance Check', status: 'inactive', steps: 5, lastRun: '1 week ago' },
]

const statusVariant = {
  active: 'accent' as const,
  inactive: 'default' as const,
  error: 'danger' as const,
}

export default function WorkflowsPage() {
  const workflows = placeholderWorkflows

  return (
    <PageContainer>
      <PageHeader
        title="Workflows"
        description="Automate document processing and analysis"
        breadcrumbs={[{ label: 'Workflows' }]}
        icon={Workflow}
        actions={
          <Button>
            <Plus className="h-4 w-4" />
            New Workflow
          </Button>
        }
      />

      {workflows.length === 0 ? (
        <EmptyState
          title="No workflows yet"
          description="Create your first workflow to automate document processing."
          icon={Workflow}
          action={<Button><Plus className="h-4 w-4" />New Workflow</Button>}
        />
      ) : (
        <div className="grid gap-4">
          {workflows.map((wf) => (
            <div
              key={wf.id}
              className="flex items-center justify-between rounded-xl border border-surface-200 bg-white p-5 shadow-sm transition-colors hover:border-primary-200"
            >
              <div className="flex items-center gap-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-50">
                  <Workflow className="h-5 w-5 text-primary-600" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-surface-900">
                    {wf.name}
                  </h3>
                  <p className="text-xs text-surface-500">
                    {wf.steps} steps &middot; Last run {wf.lastRun}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Badge
                  variant={statusVariant[wf.status as keyof typeof statusVariant]}
                >
                  {wf.status}
                </Badge>
                <button className="rounded-lg p-2 text-surface-400 hover:bg-surface-100 hover:text-surface-600">
                  <Play className="h-4 w-4" />
                </button>
                <button className="rounded-lg p-2 text-surface-400 hover:bg-surface-100 hover:text-surface-600">
                  <Settings className="h-4 w-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </PageContainer>
  )
}
