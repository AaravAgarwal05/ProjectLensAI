import type { User } from '@/types'
import { NotImplementedError } from './base'

interface LoginResponse {
  user: User
  token: string
}

interface RegisterResponse {
  user: User
  token: string
}

export const AuthService = {
  async login(_email: string, _password: string): Promise<LoginResponse> {
    throw new NotImplementedError('AuthService', 'login')
  },

  async register(
    _email: string,
    _password: string,
    _name: string
  ): Promise<RegisterResponse> {
    throw new NotImplementedError('AuthService', 'register')
  },

  async logout(): Promise<void> {
    throw new NotImplementedError('AuthService', 'logout')
  },

  async getCurrentUser(): Promise<User> {
    throw new NotImplementedError('AuthService', 'getCurrentUser')
  },

  async refreshToken(): Promise<string> {
    throw new NotImplementedError('AuthService', 'refreshToken')
  },

  async forgotPassword(_email: string): Promise<void> {
    throw new NotImplementedError('AuthService', 'forgotPassword')
  },

  async resetPassword(_token: string, _password: string): Promise<void> {
    throw new NotImplementedError('AuthService', 'resetPassword')
  },
}
