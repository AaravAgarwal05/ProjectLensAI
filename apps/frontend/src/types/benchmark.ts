export type BenchmarkStatus = 'pending' | 'running' | 'completed' | 'failed'

export interface Benchmark {
  id: string
  name: string
  description?: string
  status: BenchmarkStatus
  metrics?: BenchmarkMetrics
  createdAt: string
  updatedAt: string
}

export interface BenchmarkMetrics {
  avgLatency: number
  p95Latency: number
  p99Latency: number
  tokensPerSecond: number
  totalTokens: number
  totalRequests: number
}
