'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { motion } from 'framer-motion'
import { Icon } from '@/components/shared/icon'
import { useSidebarStore } from '@/stores/sidebar-store'

const navItems = [
  { href: '/dashboard', icon: 'dashboard', label: 'Dashboard' },
  { href: '/reports', icon: 'description', label: 'Reports' },
  { href: '/collections', icon: 'database', label: 'Collections' },
  { href: '/chat', icon: 'chat_bubble', label: 'Chat' },
  { href: '/benchmarks', icon: 'speed', label: 'Benchmarks' },
  { href: '/settings', icon: 'settings', label: 'Settings' },
]

export function Sidebar() {
  const pathname = usePathname()
  const { isOpen, setOpen } = useSidebarStore()

  const isActive = (href: string) => {
    if (href === '/dashboard') return pathname === '/dashboard'
    return pathname.startsWith(href)
  }

  return (
    <motion.aside
      className="fixed left-0 top-0 z-50 flex h-full w-[240px] flex-col gap-sm border-r border-outline-variant bg-surface-container-lowest p-md"
      animate={{ x: isOpen ? 0 : -240 }}
      transition={{ duration: 0.3, ease: 'easeInOut' }}
    >
      {/* Logo */}
      <div className="mb-lg flex items-center gap-sm">
        <div className="flex h-8 w-8 items-center justify-center rounded bg-primary">
          <Icon fill className="text-on-primary" size="20px">
            lens
          </Icon>
        </div>
        <div>
          <h1 className="font-display text-headline-md font-bold leading-none text-primary">
            ProjectLens AI
          </h1>
          <p className="mt-1 font-label-md text-[10px] uppercase tracking-widest text-outline">
            Precision Intelligence
          </p>
        </div>
      </div>

      {/* New Analysis */}
      <button
        onClick={() => setOpen(false)}
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
          <div className="h-8 w-8 overflow-hidden rounded-full border border-outline-variant bg-surface-variant">
            <img
              className="h-full w-full object-cover"
              src="https://lh3.googleusercontent.com/aida-public/AB6AXuCJbe6zybhOXXzsG_Ct2Hx163Ao3M82DmLaSzR_33nnrWHxwPhYWevjvTtA29v_6YyZ_qyhaF6ohIZvvrSFLZDH_OsZrQI-id6PQxv8ThZghp_fR14hUqRFG-7s7X1CRpgof0fpwaOQJfniI9Eo1pk6NHEiVI6ao6Ew38syBZCZ-qRooOefMh3V0Te5XtTUFv9OibUfgLzwsQjvLO1aHpnqpbzsmljeMUH8k5djvFbvNhIkeEnyAQTjx9S8PVWhdckXePxHaH5pgJd3"
              alt="User avatar"
            />
          </div>
          <div className="flex flex-col">
            <span className="text-xs font-bold text-on-surface">Alex Chen</span>
            <span className="font-label-md text-[10px] text-on-surface-variant">
              System Admin
            </span>
          </div>
        </div>
      </div>
    </motion.aside>
  )
}
