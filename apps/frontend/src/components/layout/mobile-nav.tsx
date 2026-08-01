'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import { X } from 'lucide-react'
import { useAuthStore } from '@/stores/auth-store'
import {
  LayoutDashboard,
  FileText,
  FolderOpen,
  MessageSquare,
  Settings,
  Sparkles,
} from 'lucide-react'

interface MobileNavProps {
  isOpen: boolean
  onClose: () => void
}

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/reports', label: 'Reports', icon: FileText },
  { href: '/collections', label: 'Collections', icon: FolderOpen },
  { href: '/chat', label: 'Chat', icon: MessageSquare },
  { href: '/settings', label: 'Settings', icon: Settings },
]

export function MobileNav({ isOpen, onClose }: MobileNavProps) {
  const pathname = usePathname()
  const user = useAuthStore((s) => s.user)

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 lg:hidden">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/40 transition-opacity"
        onClick={onClose}
      />

      {/* Panel */}
      <div className="fixed inset-y-0 left-0 z-50 w-72 bg-white shadow-xl">
        <div className="flex h-16 items-center justify-between border-b border-surface-200 px-4">
          <Link
            href="/dashboard"
            className="flex items-center gap-2"
            onClick={onClose}
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-primary-500 to-primary-700">
              <Sparkles className="h-4 w-4 text-white" />
            </div>
            <span className="text-lg font-bold text-surface-900">
              ProjectLens
            </span>
          </Link>
          <button
            onClick={onClose}
            className="flex h-9 w-9 items-center justify-center rounded-lg text-surface-500 hover:bg-surface-100"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <nav className="overflow-y-auto px-3 py-4">
          {navItems.map((item) => {
            const isActive = pathname === item.href || pathname.startsWith(item.href + '/')
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={onClose}
                className={cn(
                  'mb-0.5 flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary-50 text-primary-700'
                    : 'text-surface-600 hover:bg-surface-100 hover:text-surface-900'
                )}
              >
                <item.icon className="h-5 w-5 shrink-0" />
                <span>{item.label}</span>
              </Link>
            )
          })}
        </nav>

        <div className="border-t border-surface-200 px-3 py-4">
          <div className="flex items-center gap-3 px-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-100 text-sm font-semibold text-primary-700">
              {(user?.name || user?.email || 'U')
                .split(' ')
                .map((n) => n[0])
                .filter(Boolean)
                .slice(0, 2)
                .join('')
                .toUpperCase()}
            </div>
            <div className="min-w-0 text-sm">
              <p className="truncate font-medium text-surface-900">{user?.name || 'Guest'}</p>
              <p className="truncate text-surface-500">{user?.email || 'Not signed in'}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
