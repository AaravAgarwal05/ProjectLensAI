import { afterEach, describe, expect, it, vi } from 'vitest'

import { API_BASE } from '@/lib/api'
import { AuthService } from '@/services/auth'
import { jsonResponse, mockFetch } from '@/test/helpers'

afterEach(() => {
  vi.unstubAllGlobals()
})

const RAW_USER = {
  id: 'u1',
  email: 'a@b.co',
  name: 'Alice',
  role: 'user',
  created_at: '2025-01-01T00:00:00Z',
}

describe('AuthService', () => {
  it('login posts credentials and maps user to camelCase', async () => {
    const fn = mockFetch()
    fn.mockResolvedValue(jsonResponse(200, { user: RAW_USER, token: 'tok' }))

    const result = await AuthService.login('a@b.co', 'secret')

    expect(fn).toHaveBeenCalledWith(
      `${API_BASE}/auth/login`,
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ email: 'a@b.co', password: 'secret' }),
      })
    )
    expect(result.token).toBe('tok')
    expect(result.user).toEqual({
      id: 'u1',
      email: 'a@b.co',
      name: 'Alice',
      role: 'user',
      createdAt: '2025-01-01T00:00:00Z',
      updatedAt: '2025-01-01T00:00:00Z',
    })
  })

  it('register posts email, password, and name', async () => {
    const fn = mockFetch()
    fn.mockResolvedValue(jsonResponse(201, { user: RAW_USER, token: 'tok2' }))

    await AuthService.register('a@b.co', 'pw', 'Alice')

    const [, init] = fn.mock.calls[0] as [string, RequestInit]
    expect(init.method).toBe('POST')
    expect(init.body).toBe(JSON.stringify({ email: 'a@b.co', password: 'pw', name: 'Alice' }))
  })

  it('logout posts to /auth/logout', async () => {
    const fn = mockFetch()
    fn.mockResolvedValue(new Response(null, { status: 204 }))

    await AuthService.logout()

    expect(fn).toHaveBeenCalledWith(
      `${API_BASE}/auth/logout`,
      expect.objectContaining({ method: 'POST' })
    )
  })

  it('getCurrentUser maps the user response', async () => {
    const fn = mockFetch()
    fn.mockResolvedValue(jsonResponse(200, RAW_USER))

    const user = await AuthService.getCurrentUser()

    expect(fn).toHaveBeenCalledWith(`${API_BASE}/auth/me`, expect.any(Object))
    expect(user.createdAt).toBe('2025-01-01T00:00:00Z')
    expect(user.role).toBe('user')
  })

  it('refreshToken returns the new token', async () => {
    const fn = mockFetch()
    fn.mockResolvedValue(jsonResponse(200, { token: 'fresh' }))

    await expect(AuthService.refreshToken()).resolves.toBe('fresh')
  })
})
