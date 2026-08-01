'use client'

import { type ReactNode } from 'react'
import { Sidebar } from './sidebar'
import { useSidebarStore } from '@/stores/sidebar-store'

export function DashboardLayout({ children }: { children: ReactNode }) {
  const { isOpen } = useSidebarStore()

  return (
    <div className="flex min-h-screen bg-background text-on-surface">
      <Sidebar />

      <div
        className={`flex flex-1 flex-col transition-[margin] duration-300 ease-in-out ${
          isOpen ? 'ml-[240px]' : 'ml-0'
        }`}
      >
        <main className="custom-scrollbar flex-1 overflow-y-auto">
          {children}
        </main>
      </div>
    </div>
  )
}
