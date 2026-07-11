'use client'

import { PageHeader } from '@/components/shared/page-header'
import { PageContainer } from '@/components/shared/page-container'
import { SectionCard } from '@/components/shared/section-card'
import { StatCard } from '@/components/shared/stat-card'
import { Badge } from '@/components/ui/badge'
import { Shield, Users, Activity, Database, Server, AlertTriangle } from 'lucide-react'

export default function AdminPage() {
  return (
    <PageContainer>
      <PageHeader
        title="Admin"
        description="System administration and management"
        breadcrumbs={[{ label: 'Admin' }]}
        icon={Shield}
      />

      {/* Stats */}
      <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
        <StatCard title="Active Users" value="24" icon={Users} />
        <StatCard title="API Calls (24h)" value="1,847" icon={Activity} />
        <StatCard title="Storage Used" value="2.4 GB" icon={Database} />
        <StatCard title="Active Services" value="4/5" icon={Server} trend={{ value: 0, isPositive: false }} />
        <StatCard title="System Alerts" value="2" icon={AlertTriangle} trend={{ value: 1, isPositive: false }} />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Service Status */}
        <SectionCard title="Service Status">
          <div className="space-y-2">
            {[
              { name: 'API Server', status: 'healthy', uptime: '99.9%' },
              { name: 'PostgreSQL', status: 'healthy', uptime: '99.8%' },
              { name: 'Redis Cache', status: 'not configured', uptime: '-' },
              { name: 'Ollama LLM', status: 'connected', uptime: '99.5%' },
              { name: 'ChromaDB', status: 'healthy', uptime: '99.7%' },
            ].map((svc) => (
              <div
                key={svc.name}
                className="flex items-center justify-between rounded-lg border border-surface-100 p-3"
              >
                <div className="flex items-center gap-3">
                  <div
                    className={`flex h-2.5 w-2.5 rounded-full ${
                      svc.status === 'healthy'
                        ? 'bg-accent-500'
                        : svc.status === 'connected'
                          ? 'bg-primary-500'
                          : 'bg-amber-500'
                    }`}
                  />
                  <span className="text-sm font-medium text-surface-700">
                    {svc.name}
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <Badge
                    variant={
                      svc.status === 'healthy' || svc.status === 'connected'
                        ? 'accent'
                        : 'warning'
                    }
                  >
                    {svc.status}
                  </Badge>
                  <span className="text-xs text-surface-400">{svc.uptime}</span>
                </div>
              </div>
            ))}
          </div>
        </SectionCard>

        {/* Recent Activity */}
        <SectionCard title="Recent Activity">
          <div className="space-y-2">
            {[
              { action: 'User registered', user: 'john@example.com', time: '5 min ago' },
              { action: 'Report uploaded', user: 'sarah@example.com', time: '12 min ago' },
              { action: 'Chat session created', user: 'mike@example.com', time: '30 min ago' },
              { action: 'Workflow triggered', user: 'System', time: '1 hour ago' },
              { action: 'Collection updated', user: 'anna@example.com', time: '2 hours ago' },
            ].map((event, i) => (
              <div
                key={i}
                className="flex items-center justify-between rounded-lg border border-surface-100 p-3"
              >
                <div>
                  <p className="text-sm font-medium text-surface-700">
                    {event.action}
                  </p>
                  <p className="text-xs text-surface-400">{event.user}</p>
                </div>
                <span className="text-xs text-surface-400">{event.time}</span>
              </div>
            ))}
          </div>
        </SectionCard>
      </div>
    </PageContainer>
  )
}
