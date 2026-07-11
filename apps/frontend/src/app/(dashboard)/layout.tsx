/**
 * Dashboard group layout — children are already wrapped in DashboardLayout
 * by each page (to pass custom TopNav props like searchPlaceholder).
 * This layout just provides the route-group boundary for Next.js.
 */
export default function AuthenticatedLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return <>{children}</>
}
