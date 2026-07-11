'use client'

import { type ReactNode } from 'react'
import { Icon } from '@/components/shared/icon'
import { useSidebarStore } from '@/stores/sidebar-store'

interface TopNavProps {
  /** Custom left content (e.g. save indicator for chat) */
  leftExtra?: ReactNode
  /** Search placeholder text */
  searchPlaceholder?: string
  /** Hide the search bar */
  hideSearch?: boolean
  /** Hide Doc/Community links */
  hideLinks?: boolean
  /** Extra right-side actions */
  rightExtra?: ReactNode
}

export function TopNav({
  leftExtra,
  searchPlaceholder = 'Search across intelligence...',
  hideSearch = false,
  hideLinks = false,
  rightExtra,
}: TopNavProps) {
  const { isOpen, toggle } = useSidebarStore()

  return (
    <header className="sticky top-0 z-40 flex h-16 items-center justify-between border-b border-outline-variant bg-surface/80 px-xl backdrop-blur-xl">
      <div className="flex flex-1 items-center gap-xl">
        {/* Sidebar toggle */}
        <button
          onClick={toggle}
          className="text-on-surface-variant transition-colors hover:text-on-surface"
          aria-label={isOpen ? 'Close sidebar' : 'Open sidebar'}
        >
          <Icon>{isOpen ? 'menu' : 'menu_open'}</Icon>
        </button>

        {/* Left extra (e.g. save indicator) */}
        {leftExtra}

        {/* Search */}
        {!hideSearch && (
          <div className="relative w-full max-w-md">
            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-[18px] text-outline">
              search
            </span>
            <input
              type="text"
              placeholder={searchPlaceholder}
              className="w-full rounded-lg border border-outline-variant bg-surface-container-lowest py-1.5 pl-10 pr-md font-body-md outline-none transition-all focus:ring-1 focus:ring-primary/50"
            />
          </div>
        )}

        {/* Links */}
        {!hideLinks && (
          <nav className="hidden items-center gap-lg md:flex">
            <a
              href="#"
              className="font-body-md text-on-surface-variant transition-colors hover:text-on-surface"
            >
              Docs
            </a>
            <a
              href="#"
              className="font-body-md text-on-surface-variant transition-colors hover:text-on-surface"
            >
              Community
            </a>
          </nav>
        )}
      </div>

      {/* Right side */}
      <div className="flex items-center gap-md">
        {rightExtra}

        <button className="text-on-surface-variant transition-colors hover:text-on-surface">
          <Icon>notifications</Icon>
        </button>
        <button className="text-on-surface-variant transition-colors hover:text-on-surface">
          <Icon>dark_mode</Icon>
        </button>
        <div className="h-8 w-8 overflow-hidden rounded-full border border-outline-variant bg-surface-container-high">
          <img
            className="h-full w-full object-cover"
            src="https://lh3.googleusercontent.com/aida-public/AB6AXuD-FoKcrUm_7xyYyYdII-F9j2mF9UOPmrMdIuGhbAawKW7FOmoL69cYBb99drngW-Q97adgPtcJsLx_x5zO7vnSvXK5x2qXBXiXseB_pCylhdI3kI50HtbhGfvn-g6Ye3KAshyNirLFnxflF6qcBcB1FK2dEDokoto2Ha0yhxhFvDzpTe8-X_4yJUTP-uyTxVpF1Vb4qY308SNRK210gjFhHMoIfwpyYGMBvyfEailEwSRK_4nkWrS8PR1Tdr6aclU913J2J5u3vtj3"
            alt="User avatar"
          />
        </div>
      </div>
    </header>
  )
}
