'use client'

import { useEffect, useState, useCallback, useRef } from 'react'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import { DashboardLayout } from '@/components/layout/dashboard-layout'
import { Icon } from '@/components/shared/icon'
import { AuthService } from '@/services/auth'
import { useAuthStore } from '@/stores/auth-store'
import type { User } from '@/types'
import { ApiError } from '@/lib/api'

/* ─── animation helpers ─── */

const fadeUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.45, ease: 'easeOut' as const },
}

const containerVariants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.07 } },
}

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { duration: 0.45, ease: 'easeOut' as const } },
}

/* ─── helpers ─── */

function getInitials(name: string): string {
  return name
    .split(' ')
    .map((n) => n[0])
    .filter(Boolean)
    .slice(0, 2)
    .join('')
    .toUpperCase()
}

function formatDate(dateStr: string): string {
  try {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    })
  } catch {
    return dateStr
  }
}

/* ─── role badge color ─── */

interface RoleBadge { ring: string; text: string; dot: string }

function badgeForRole(role: string): RoleBadge {
  if (role === 'admin') return { ring: 'ring-primary/30', text: 'text-primary', dot: 'bg-primary' }
  if (role === 'viewer') return { ring: 'ring-tertiary/30', text: 'text-tertiary', dot: 'bg-tertiary' }
  return { ring: 'ring-secondary/30', text: 'text-secondary', dot: 'bg-secondary' }
}

/* ─── page ─── */

export default function DashboardPage() {
  const { user, setUser, reset: resetAuth, isLoading, setLoading } = useAuthStore()
  const [error, setError] = useState('')
  const [loggingOut, setLoggingOut] = useState(false)
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false)
  const loggingOutRef = useRef(false)

  useEffect(() => {
    if (user || loggingOutRef.current) return

    setLoading(true)
    setError('')
    AuthService.getCurrentUser()
      .then((u: User) => setUser(u))
      .catch((err: Error) => {
        setError(err.message ?? 'Failed to load user')
        // 401 / token expired — redirect to login
        const status = err instanceof ApiError ? err.status : 0
        if (status === 401 || err.message.toLowerCase().includes('token')) {
          resetAuth()
          window.location.href = '/auth/login'
        }
      })
      .finally(() => setLoading(false))
  }, [user, setUser, setLoading, resetAuth])

  const handleLogout = useCallback(async () => {
    loggingOutRef.current = true
    setLoggingOut(true)
    try {
      await AuthService.logout()
    } catch {
      // swallow
    }
    resetAuth()
    // Hard redirect — clears all React state, prevents re-fetch race
    window.location.href = '/auth/login'
  }, [resetAuth])

  const badge = badgeForRole(user?.role ?? 'user')

  return (
    <DashboardLayout>
      <div className="p-xl">
        {/* ─── Page Header ─── */}
        <motion.div className="mb-xl flex items-start justify-between" {...fadeUp}>
          <div>
            <h1 className="font-headline-lg font-bold text-on-surface">Dashboard</h1>
            <p className="font-body-md text-on-surface-variant">Welcome back, {user?.name?.split(' ')[0] ?? 'User'}.</p>
          </div>
        </motion.div>

        {isLoading && (
          <div className="flex items-center justify-center py-32">
            <div className="flex flex-col items-center gap-md">
              <span className="inline-block h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
              <p className="font-body-md text-on-surface-variant">Loading profile…</p>
            </div>
          </div>
        )}

        {error && !isLoading && (
          <div className="flex items-center justify-center py-32">
            <div className="glass-card max-w-md rounded-xl p-xl text-center">
              <Icon className="text-error mb-md" size="40px">error_outline</Icon>
              <h2 className="font-headline-md text-on-surface mb-sm">Something went wrong</h2>
              <p className="font-body-md text-on-surface-variant mb-lg">{error}</p>
              <button
                onClick={() => window.location.reload()}
                className="rounded-lg bg-primary px-lg py-sm font-headline-md text-on-primary transition-colors hover:bg-primary-fixed-dim"
              >
                Try Again
              </button>
            </div>
          </div>
        )}

        {user && !isLoading && (
          <motion.div
            className="space-y-xl"
            variants={containerVariants}
            initial="hidden"
            animate="show"
          >
            {/* ─── Profile Card ─── */}
            <motion.div variants={itemVariants}>
              <div className="glass-card ai-glow relative overflow-hidden rounded-2xl">
                <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-secondary/5 pointer-events-none" />

                <div className="relative z-10 flex flex-col items-center gap-lg p-xl sm:flex-row sm:items-start">
                  {/* Avatar */}
                  <div className="relative shrink-0">
                    <div className="flex h-24 w-24 items-center justify-center rounded-2xl bg-gradient-to-br from-primary to-secondary text-[32px] font-bold text-on-primary shadow-lg shadow-primary/20">
                      {getInitials(user.name)}
                    </div>
                    <div className="absolute -bottom-1 -right-1 rounded-full border-2 border-surface bg-emerald-500 p-1.5 shadow-lg">
                      <div className="h-2 w-2 rounded-full bg-emerald-500 shadow-[0_0_6px_rgba(34,197,94,0.6)]" />
                    </div>
                  </div>

                  {/* Info */}
                  <div className="flex-1 text-center sm:text-left">
                    <div className="flex flex-col items-center gap-sm sm:flex-row sm:items-center">
                      <h2 className="font-display text-headline-lg text-on-surface">{user.name}</h2>
                      <span
                        className={`inline-flex items-center gap-1 rounded-full px-3 py-0.5 font-label-md text-[11px] uppercase tracking-wider ring-1 ${badge.ring} ${badge.text}`}
                      >
                        <span className={`h-1.5 w-1.5 rounded-full ${badge.dot}`} />
                        {user.role}
                      </span>
                    </div>
                    <p className="font-body-md text-on-surface-variant mt-1">{user.email}</p>

                    <div className="mt-lg flex flex-wrap items-center gap-x-xl gap-y-sm">
                      <div className="flex items-center gap-sm">
                        <Icon className="text-outline" size="16px">calendar_today</Icon>
                        <span className="font-body-md text-on-surface-variant">
                          Member since <span className="text-on-surface">{formatDate(user.createdAt)}</span>
                        </span>
                      </div>
                      <div className="flex items-center gap-sm">
                        <Icon className="text-outline" size="16px">verified</Icon>
                        <span className="font-body-md text-emerald-500">Active account</span>
                      </div>
                    </div>
                  </div>

                  {/* Logout */}
                  <div className="shrink-0 self-start">
                    <button
                      onClick={() => setShowLogoutConfirm(true)}
                      className="flex items-center gap-2 rounded-lg border border-outline-variant px-md py-2 font-label-md text-on-surface-variant transition-colors hover:border-error/50 hover:text-error hover:bg-error/5"
                    >
                      <Icon size="16px">logout</Icon>
                      Sign Out
                    </button>
                  </div>
                </div>
              </div>
            </motion.div>

            {/* ─── Account Details Grid ─── */}
            <div className="grid grid-cols-1 gap-xl md:grid-cols-2 lg:grid-cols-3">
              {/* Account Info */}
              <motion.div variants={itemVariants} className="glass-card rounded-xl p-lg">
                <div className="mb-md flex items-center gap-sm">
                  <Icon className="text-primary" size="20px">badge</Icon>
                  <h3 className="font-display text-headline-sm text-on-surface">Account Info</h3>
                </div>
                <div className="space-y-md">
                  <div>
                    <p className="font-label-md text-[10px] uppercase tracking-wider text-outline">Full Name</p>
                    <p className="font-body-md text-on-surface">{user.name}</p>
                  </div>
                  <div>
                    <p className="font-label-md text-[10px] uppercase tracking-wider text-outline">Email Address</p>
                    <p className="font-body-md text-on-surface">{user.email}</p>
                  </div>
                  <div>
                    <p className="font-label-md text-[10px] uppercase tracking-wider text-outline">Role</p>
                    <p className="font-body-md text-on-surface capitalize">{user.role}</p>
                  </div>
                  <div>
                    <p className="font-label-md text-[10px] uppercase tracking-wider text-outline">Account ID</p>
                    <p className="font-code-sm text-on-surface-variant break-all">{user.id}</p>
                  </div>
                </div>
              </motion.div>

              {/* Security */}
              <motion.div variants={itemVariants} className="glass-card rounded-xl p-lg">
                <div className="mb-md flex items-center gap-sm">
                  <Icon className="text-secondary" size="20px">security</Icon>
                  <h3 className="font-display text-headline-sm text-on-surface">Security</h3>
                </div>
                <div className="space-y-md">
                  <Link
                    href="/settings"
                    className="flex items-center justify-between rounded-lg bg-surface-container-low p-md transition-colors hover:bg-surface-container-high group"
                  >
                    <div>
                      <p className="font-body-md text-on-surface">Password</p>
                      <p className="font-label-md text-[10px] text-outline">Last changed 30 days ago</p>
                    </div>
                    <span className="rounded-lg border border-outline-variant px-md py-1 font-label-md text-primary transition-colors group-hover:bg-primary-container/20">
                      Update
                    </span>
                  </Link>
                  <Link
                    href="/settings"
                    className="flex items-center justify-between rounded-lg bg-surface-container-low p-md transition-colors hover:bg-surface-container-high group"
                  >
                    <div>
                      <p className="font-body-md text-on-surface">Two-Factor Auth</p>
                      <p className="font-label-md text-[10px] text-outline">Not enabled</p>
                    </div>
                    <span className="rounded-lg border border-outline-variant px-md py-1 font-label-md text-primary transition-colors group-hover:bg-primary-container/20">
                      Enable
                    </span>
                  </Link>
                  <Link
                    href="/settings"
                    className="flex items-center justify-between rounded-lg bg-surface-container-low p-md transition-colors hover:bg-surface-container-high group"
                  >
                    <div>
                      <p className="font-body-md text-on-surface">Active Sessions</p>
                      <p className="font-label-md text-[10px] text-outline">1 session</p>
                    </div>
                    <span className="rounded-lg border border-outline-variant px-md py-1 font-label-md text-primary transition-colors group-hover:bg-primary-container/20">
                      Manage
                    </span>
                  </Link>
                </div>
              </motion.div>

              {/* Quick Actions */}
              <motion.div variants={itemVariants} className="glass-card rounded-xl p-lg">
                <div className="mb-md flex items-center gap-sm">
                  <Icon className="text-tertiary" size="20px">bolt</Icon>
                  <h3 className="font-display text-headline-sm text-on-surface">Quick Actions</h3>
                </div>
                <div className="space-y-sm">
                  <Link
                    href="/reports"
                    className="flex items-center gap-md rounded-lg bg-surface-container-low p-md transition-colors hover:bg-surface-container-high group"
                  >
                    <Icon className="text-primary" size="20px">upload_file</Icon>
                    <span className="flex-1 text-left font-body-md text-on-surface">Upload a Report</span>
                    <Icon className="text-outline group-hover:text-on-surface transition-colors" size="16px">arrow_forward_ios</Icon>
                  </Link>
                  <Link
                    href="/chat"
                    className="flex items-center gap-md rounded-lg bg-surface-container-low p-md transition-colors hover:bg-surface-container-high group"
                  >
                    <Icon className="text-secondary" size="20px">chat</Icon>
                    <span className="flex-1 text-left font-body-md text-on-surface">Start New Chat</span>
                    <Icon className="text-outline group-hover:text-on-surface transition-colors" size="16px">arrow_forward_ios</Icon>
                  </Link>
                  <Link
                    href="/settings"
                    className="flex items-center gap-md rounded-lg bg-surface-container-low p-md transition-colors hover:bg-surface-container-high group"
                  >
                    <Icon className="text-tertiary" size="20px">settings</Icon>
                    <span className="flex-1 text-left font-body-md text-on-surface">Account Settings</span>
                    <Icon className="text-outline group-hover:text-on-surface transition-colors" size="16px">arrow_forward_ios</Icon>
                  </Link>
                </div>
              </motion.div>
            </div>

            {/* ─── Recent Activity ─── */}
            <motion.div variants={itemVariants}>
              <div className="glass-card rounded-xl p-lg">
                <div className="mb-md flex items-center justify-between">
                  <div className="flex items-center gap-sm">
                    <Icon className="text-primary" size="20px">history</Icon>
                    <h3 className="font-display text-headline-sm text-on-surface">Recent Activity</h3>
                  </div>
                  <Link
                    href="/settings"
                    className="font-label-md text-[11px] uppercase tracking-wider text-primary hover:underline"
                  >
                    View All
                  </Link>
                </div>
                <div className="space-y-sm">
                  {[
                    { icon: 'person', text: 'Account created', time: formatDate(user.createdAt), color: 'text-primary' },
                    { icon: 'login', text: 'Last login', time: 'Today', color: 'text-secondary' },
                  ].map((activity, idx) => (
                    <div key={idx} className="flex items-center gap-md rounded-lg bg-surface-container-low p-md">
                      <div className={`flex h-9 w-9 items-center justify-center rounded-lg bg-surface-container-high ${activity.color}`}>
                        <Icon size="18px">{activity.icon}</Icon>
                      </div>
                      <div className="flex-1">
                        <p className="font-body-md text-on-surface">{activity.text}</p>
                        <p className="font-label-md text-[10px] text-outline">{activity.time}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}

        {/* ─── Logout Confirmation Modal ─── */}
        <AnimatePresence>
          {showLogoutConfirm && (
            <motion.div
              className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <motion.div
                className="glass-card mx-md w-full max-w-sm rounded-2xl p-xl"
                initial={{ scale: 0.9, opacity: 0, y: 20 }}
                animate={{ scale: 1, opacity: 1, y: 0 }}
                exit={{ scale: 0.9, opacity: 0, y: 20 }}
                transition={{ duration: 0.2 }}
              >
                <div className="mb-md flex h-12 w-12 items-center justify-center rounded-full bg-error-container/30">
                  <Icon className="text-error" size="24px">logout</Icon>
                </div>
                <h2 className="font-display text-headline-md text-on-surface mb-sm">Sign Out</h2>
                <p className="font-body-md text-on-surface-variant mb-lg">
                  Are you sure you want to sign out? You&apos;ll need to log in again to access your account.
                </p>
                <div className="flex gap-md">
                  <button
                    onClick={() => setShowLogoutConfirm(false)}
                    disabled={loggingOut}
                    className="flex-1 rounded-lg border border-outline-variant px-lg py-sm font-headline-md text-on-surface transition-colors hover:bg-surface-container-high disabled:opacity-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleLogout}
                    disabled={loggingOut}
                    className="flex-1 rounded-lg bg-error px-lg py-sm font-headline-md text-on-error transition-colors hover:bg-error/90 disabled:opacity-50 flex items-center justify-center gap-sm"
                  >
                    {loggingOut ? (
                      <>
                        <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-on-error border-t-transparent" />
                        Signing out…
                      </>
                    ) : (
                      'Sign Out'
                    )}
                  </button>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </DashboardLayout>
  )
}
