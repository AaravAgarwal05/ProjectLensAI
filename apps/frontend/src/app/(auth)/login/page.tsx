'use client'

import { useState } from 'react'
import { Sparkles, Loader2, Eye, EyeOff } from 'lucide-react'
import Link from 'next/link'

export default function LoginPage() {
  const [isLoading, setIsLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    // Simulate API call
    setTimeout(() => setIsLoading(false), 1500)
  }

  return (
    <div className="flex min-h-screen">
      {/* Left - Brand panel */}
      <div className="hidden flex-1 flex-col justify-between bg-gradient-to-br from-primary-900 via-primary-800 to-surface-900 p-12 lg:flex">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-white/10 backdrop-blur-sm">
            <Sparkles className="h-4 w-4 text-white" />
          </div>
          <span className="text-lg font-bold text-white">ProjectLens</span>
        </div>
        <div className="max-w-md">
          <blockquote className="text-xl font-medium leading-relaxed text-white/90">
            &ldquo;ProjectLens transformed how our team analyzes documents.
            The AI-powered insights save us hours every week.&rdquo;
          </blockquote>
          <div className="mt-6 flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-white/10 text-sm font-medium text-white">
              SK
            </div>
            <div>
              <p className="text-sm font-semibold text-white">Sarah Kim</p>
              <p className="text-xs text-white/60">Product Manager, TechCorp</p>
            </div>
          </div>
        </div>
        <p className="text-sm text-white/40">
          &copy; {new Date().getFullYear()} ProjectLens AI
        </p>
      </div>

      {/* Right - Login form */}
      <div className="flex flex-1 items-center justify-center px-6 py-12 sm:px-12">
        <div className="w-full max-w-sm">
          <div className="mb-10 text-center lg:text-left">
            <h1 className="text-2xl font-bold tracking-tight text-surface-900">
              Welcome back
            </h1>
            <p className="mt-2 text-sm text-surface-600">
              Sign in to your account to continue
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label
                htmlFor="email"
                className="mb-1.5 block text-sm font-medium text-surface-700"
              >
                Email address
              </label>
              <input
                id="email"
                type="email"
                required
                className="input-field"
                placeholder="you@company.com"
                value={formData.email}
                onChange={(e) =>
                  setFormData({ ...formData, email: e.target.value })
                }
              />
            </div>

            <div>
              <label
                htmlFor="password"
                className="mb-1.5 block text-sm font-medium text-surface-700"
              >
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  required
                  className="input-field pr-10"
                  placeholder="Enter your password"
                  value={formData.password}
                  onChange={(e) =>
                    setFormData({ ...formData, password: e.target.value })
                  }
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-surface-400 hover:text-surface-600"
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  className="h-4 w-4 rounded border-surface-300 text-primary-600 focus:ring-primary-500"
                />
                <span className="text-sm text-surface-600">Remember me</span>
              </label>
              <button
                type="button"
                className="text-sm font-medium text-primary-600 hover:text-primary-700"
              >
                Forgot password?
              </button>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="btn-primary w-full"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Signing in...
                </>
              ) : (
                'Sign in'
              )}
            </button>
          </form>

          <p className="mt-8 text-center text-sm text-surface-600">
            Don&apos;t have an account?{' '}
            <Link
              href="/register"
              className="font-semibold text-primary-600 hover:text-primary-700"
            >
              Create one
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
