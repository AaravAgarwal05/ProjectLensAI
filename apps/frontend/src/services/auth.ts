import type { User } from '@/types'
import { apiRequest } from '@/lib/api'

// ─── Raw backend response types (snake_case) ───

interface UserResponse {
  id: string
  email: string
  name: string
  role: string
  created_at: string
}

interface AuthResponseRaw {
  user: UserResponse
  token: string
}

// ─── Mapper ───

function mapUser(u: UserResponse): User {
  return {
    id: u.id,
    email: u.email,
    name: u.name,
    role: u.role as User['role'],
    createdAt: u.created_at,
    updatedAt: u.created_at,
  }
}

// ─── Service ───

export const AuthService = {
  async login(email: string, password: string): Promise<{ user: User; token: string }> {
    const data = await apiRequest<AuthResponseRaw>('/auth/login', {
      method: 'POST',
      body: { email, password },
    })
    // Session is carried by the HttpOnly cookie set by the backend.
    return { user: mapUser(data.user), token: data.token }
  },

  async register(
    email: string,
    password: string,
    name: string
  ): Promise<{ user: User; token: string }> {
    const data = await apiRequest<AuthResponseRaw>('/auth/register', {
      method: 'POST',
      body: { email, password, name },
    })
    return { user: mapUser(data.user), token: data.token }
  },

  async logout(): Promise<void> {
    // Backend expires the HttpOnly cookie + bumps token_version.
    await apiRequest('/auth/logout', { method: 'POST' })
  },

  async getCurrentUser(): Promise<User> {
    const data = await apiRequest<UserResponse>('/auth/me')
    return mapUser(data)
  },

  async refreshToken(): Promise<string> {
    const data = await apiRequest<{ token: string }>('/auth/refresh', {
      method: 'POST',
    })
    return data.token
  },

  async forgotPassword(_email: string): Promise<void> {
    // Not yet implemented on backend
    console.warn('forgotPassword not implemented on backend')
  },

  async resetPassword(_token: string, _password: string): Promise<void> {
    // Not yet implemented on backend
    console.warn('resetPassword not implemented on backend')
  },
}
