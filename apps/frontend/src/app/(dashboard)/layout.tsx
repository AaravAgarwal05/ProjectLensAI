import { RouteGuard } from '@/components/auth/route-guard'

/**
 * Dashboard group layout — children are already wrapped in DashboardLayout
 * by each page. This layout provides the route-group boundary for Next.js
 * and guards the group behind an auth check.
 */
export default function AuthenticatedLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return <RouteGuard>{children}</RouteGuard>
}
