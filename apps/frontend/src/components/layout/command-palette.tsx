'use client'

import { useEffect, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { Search, FileText, MessageSquare, Settings, LayoutDashboard } from 'lucide-react'

interface CommandItem {
  id: string
  label: string
  href: string
  icon: React.ReactNode
  category: string
}

const commands: CommandItem[] = [
  { id: '1', label: 'Go to Dashboard', href: '/dashboard', icon: <LayoutDashboard className="h-4 w-4" />, category: 'Navigation' },
  { id: '2', label: 'View Reports', href: '/reports', icon: <FileText className="h-4 w-4" />, category: 'Navigation' },
  { id: '3', label: 'Open Chat', href: '/chat', icon: <MessageSquare className="h-4 w-4" />, category: 'Navigation' },
  { id: '4', label: 'Settings', href: '/settings', icon: <Settings className="h-4 w-4" />, category: 'Navigation' },
]

export function CommandPalette() {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const router = useRouter()

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        setOpen((prev) => !prev)
      }
      if (e.key === 'Escape' && open) {
        setOpen(false)
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [open])

  const filtered = query
    ? commands.filter((cmd) =>
        cmd.label.toLowerCase().includes(query.toLowerCase())
      )
    : commands

  const handleSelect = useCallback(
    (href: string) => {
      setOpen(false)
      setQuery('')
      router.push(href)
    },
    [router]
  )

  if (!open) return null

  return (
    <div className="fixed inset-0 z-[100]">
      <div
        className="fixed inset-0 bg-black/40 backdrop-blur-sm"
        onClick={() => setOpen(false)}
      />
      <div className="fixed left-1/2 top-[15%] w-full max-w-lg -translate-x-1/2">
        <div className="overflow-hidden rounded-xl border border-surface-200 bg-white shadow-2xl">
          <div className="flex items-center border-b border-surface-200 px-4">
            <Search className="h-5 w-5 text-surface-400" />
            <input
              autoFocus
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search pages and commands..."
              className="flex-1 border-0 bg-transparent px-3 py-3.5 text-sm text-surface-900 placeholder-surface-400 focus:outline-none"
            />
            <kbd className="rounded border border-surface-200 bg-surface-50 px-1.5 py-0.5 text-[10px] text-surface-400">
              ESC
            </kbd>
          </div>
          <div className="max-h-72 overflow-y-auto p-2">
            {filtered.length === 0 && (
              <p className="px-3 py-8 text-center text-sm text-surface-500">
                No results found.
              </p>
            )}
            {filtered.map((cmd) => (
              <button
                key={cmd.id}
                onClick={() => handleSelect(cmd.href)}
                className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-surface-700 transition-colors hover:bg-surface-100"
              >
                <span className="flex h-7 w-7 items-center justify-center rounded-md bg-surface-100 text-surface-500">
                  {cmd.icon}
                </span>
                <span>{cmd.label}</span>
                <span className="ml-auto text-xs text-surface-400">
                  {cmd.category}
                </span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
