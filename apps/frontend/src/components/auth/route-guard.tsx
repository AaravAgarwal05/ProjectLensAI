'use client'

import { useEffect, useState } from 'react'

import { useRouter } from 'next/navigation'

import { getAuthToken } from '@/lib/api'

/**
 * Client-side auth guard for the authenticated route group.
 *
 * Redirects to /auth/login when no token is present, so protected pages
 * don't render in a broken, unauthenticated state. (Defense-in-depth only —
 * the real boundary is the API's `get_current_user` dependency.)
 */
export function RouteGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const [authed, setAuthed] = useState(false)

  useEffect(() => {
    if (!getAuthToken()) {
      router.replace('/auth/login')
      return
    }
    setAuthed(true)
  }, [router])

  if (!authed) return null
  return <>{children}</>
}
