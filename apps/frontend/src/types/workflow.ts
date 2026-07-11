export type WorkflowStatus = 'active' | 'inactive' | 'error'

export interface Workflow {
  id: string
  name: string
  description?: string
  status: WorkflowStatus
  steps: WorkflowStep[]
  createdAt: string
  updatedAt: string
}

export interface WorkflowStep {
  id: string
  name: string
  type: string
  config: Record<string, unknown>
}

export interface WorkflowRun {
  id: string
  workflowId: string
  status: 'running' | 'completed' | 'failed'
  startedAt: string
  completedAt?: string
  result?: Record<string, unknown>
}
