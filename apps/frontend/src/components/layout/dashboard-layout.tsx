'use client'

import { type ReactNode } from 'react'
import { Sidebar } from './sidebar'
import { TopNav } from './top-nav'
import { useSidebarStore } from '@/stores/sidebar-store'

interface DashboardLayoutProps {
  children: ReactNode
  searchPlaceholder?: string
  hideSearch?: boolean
  hideLinks?: boolean
  leftExtra?: ReactNode
  rightExtra?: ReactNode
}

export function DashboardLayout({
  children,
  searchPlaceholder,
  hideSearch,
  hideLinks,
  leftExtra,
  rightExtra,
}: DashboardLayoutProps) {
  const { isOpen } = useSidebarStore()

  return (
    <div className="flex min-h-screen bg-background text-on-surface">
      <Sidebar />

      <div
        className={`flex flex-1 flex-col transition-[margin] duration-300 ease-in-out ${
          isOpen ? 'ml-[240px]' : 'ml-0'
        }`}
      >
        <TopNav
          searchPlaceholder={searchPlaceholder}
          hideSearch={hideSearch}
          hideLinks={hideLinks}
          leftExtra={leftExtra}
          rightExtra={rightExtra}
        />

        <main className="custom-scrollbar flex-1 overflow-y-auto">
          {children}
        </main>
      </div>
    </div>
  )
}
