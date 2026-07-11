export type UserRole = 'admin' | 'user' | 'viewer'

export interface User {
  id: string
  email: string
  name: string
  avatar?: string
  role: UserRole
  createdAt: string
  updatedAt: string
}
