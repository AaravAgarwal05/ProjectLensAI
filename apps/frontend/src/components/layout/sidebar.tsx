'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { motion } from 'framer-motion'
import { Icon } from '@/components/shared/icon'
import { useSidebarStore } from '@/stores/sidebar-store'
import { useAuthStore } from '@/stores/auth-store'

const navItems = [
  { href: '/dashboard', icon: 'dashboard', label: 'Dashboard' },
  { href: '/reports', icon: 'description', label: 'Reports' },
  { href: '/collections', icon: 'database', label: 'Collections' },
  { href: '/chat', icon: 'chat_bubble', label: 'Chat' },
  { href: '/settings', icon: 'settings', label: 'Settings' },
]

export function Sidebar() {
  const pathname = usePathname()
  const { isOpen, setOpen } = useSidebarStore()
  const user = useAuthStore((s) => s.user)

  const isActive = (href: string) => {
    if (href === '/dashboard') return pathname === '/dashboard'
    return pathname.startsWith(href)
  }

  return (
    <>
      {/* Open tab — shown only when sidebar is closed */}
      {!isOpen && (
        <button
          onClick={() => setOpen(true)}
          aria-label="Open sidebar"
          className="fixed left-0 top-4 z-50 flex h-12 w-12 items-center justify-center rounded-r-lg border border-l-0 border-outline-variant bg-surface-container-lowest text-on-surface-variant shadow-lg transition-colors hover:bg-surface-container-high hover:text-on-surface"
        >
          <Icon size="24px">menu</Icon>
        </button>
      )}

      <motion.aside
        className="fixed left-0 top-0 z-50 flex h-full w-[240px] flex-col gap-sm border-r border-outline-variant bg-surface-container-lowest p-md"
        animate={{ x: isOpen ? 0 : -240 }}
        transition={{ duration: 0.3, ease: 'easeInOut' }}
      >
        {/* Header: logo + close */}
        <div className="mb-lg flex items-start gap-sm">
          <div className="flex flex-1 items-center gap-sm">
            <img
              src="/Logo.png"
              alt="ProjectLens AI"
              className="h-9 w-9 rounded-full object-cover"
            />
            <div>
              <h1 className="font-logo text-headline-md font-semibold leading-none text-primary">
                ProjectLens AI
              </h1>
              <p className="mt-1 font-label-md text-[10px] uppercase tracking-widest text-outline">
                Precision Intelligence
              </p>
            </div>
          </div>
          {/* Close button */}
          <button
            onClick={() => setOpen(false)}
            aria-label="Close sidebar"
            className="flex h-8 w-8 items-center justify-center rounded text-on-surface-variant transition-colors hover:bg-surface-container-high hover:text-on-surface"
          >
            <Icon size="20px">close</Icon>
          </button>
        </div>

      {/* New Analysis */}
      <button
        className="mb-md flex w-full items-center justify-center gap-2 rounded bg-primary py-sm font-body-md font-bold text-on-primary transition-opacity hover:opacity-90"
      >
        <Icon size="18px">add</Icon>
        New Analysis
      </button>

      {/* Navigation */}
      <nav className="flex-1 space-y-1">
        {navItems.map((item) => {
          const active = isActive(item.href)
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-md rounded p-sm font-body-md transition-colors ${
                active
                  ? 'border-r-2 border-primary bg-primary-container/10 font-bold text-primary'
                  : 'text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface'
              }`}
            >
              <Icon
                fill={active}
                size="20px"
                className={active ? '' : ''}
              >
                {item.icon}
              </Icon>
              <span>{item.label}</span>
            </Link>
          )
        })}
      </nav>

      {/* Bottom section */}
      <div className="mt-auto space-y-1 border-t border-outline-variant pt-md">
        <Link
          href="#"
          className="flex items-center gap-md rounded p-sm text-on-surface-variant transition-colors hover:bg-surface-container-high hover:text-on-surface"
        >
          <Icon size="20px">help</Icon>
          <span className="font-body-md">Support</span>
        </Link>
        <Link
          href="#"
          className="flex items-center gap-md rounded p-sm text-on-surface-variant transition-colors hover:bg-surface-container-high hover:text-on-surface"
        >
          <Icon size="20px">code</Icon>
          <span className="font-body-md">API Keys</span>
        </Link>

        {/* User profile */}
        <div className="mt-md flex items-center gap-sm px-sm py-sm">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-outline-variant bg-surface-variant font-label-md text-xs font-bold text-on-surface-variant">
            {(user?.name || user?.email || 'U')
              .split(' ')
              .map((n) => n[0])
              .filter(Boolean)
              .slice(0, 2)
              .join('')
              .toUpperCase()}
          </div>
          <div className="flex min-w-0 flex-col">
            <span className="truncate text-xs font-bold text-on-surface">
              {user?.name || 'Guest'}
            </span>
            <span className="truncate font-label-md text-[10px] text-on-surface-variant">
              {user?.email || 'Not signed in'}
            </span>
          </div>
        </div>
      </div>
      </motion.aside>
    </>
  )
}
