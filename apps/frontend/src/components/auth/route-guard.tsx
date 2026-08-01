'use client'

import { useEffect, useState } from 'react'

import { useRouter } from 'next/navigation'

import { AuthService } from '@/services/auth'

/**
 * Client-side auth guard for the authenticated route group.
 *
 * Probes GET /auth/me to confirm the session cookie is valid, and redirects
 * to /auth/login when it isn't. (Defense-in-depth only — the real boundary
 * is the API's `get_current_user` dependency.)
 */
export function RouteGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const [authed, setAuthed] = useState(false)

  useEffect(() => {
    let cancelled = false

    AuthService.getCurrentUser()
      .then(() => {
        if (!cancelled) setAuthed(true)
      })
      .catch(() => {
        if (!cancelled) router.replace('/auth/login')
      })

    return () => {
      cancelled = true
    }
  }, [router])

  if (!authed) return null
  return <>{children}</>
}
