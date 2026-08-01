'use client'

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { motion, AnimatePresence } from 'framer-motion'

type ToastVariant = 'success' | 'error' | 'warning' | 'info'

interface ToastAction {
  label: string
  onClick: () => void
  variant?: 'confirm' | 'cancel'
}

interface Toast {
  id: string
  message: string
  variant: ToastVariant
  duration?: number
  actions?: ToastAction[]
}

interface ToastContextValue {
  toasts: Toast[]
  addToast: (message: string, variant?: ToastVariant, duration?: number) => void
  confirmToast: (
    message: string,
    onConfirm: () => void,
    confirmLabel?: string
  ) => void
  removeToast: (id: string) => void
}

const ToastContext = createContext<ToastContextValue | null>(null)

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be within ToastProvider')
  return ctx
}

interface ToastProviderProps {
  children: ReactNode
}

export function ToastProvider({ children }: ToastProviderProps) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  const addToast = useCallback(
    (message: string, variant: ToastVariant = 'info', duration = 4000) => {
      const id = Math.random().toString(36).substring(2, 10)
      setToasts((prev) => [...prev, { id, message, variant, duration }])

      if (duration > 0) {
        setTimeout(() => {
          setToasts((prev) => prev.filter((t) => t.id !== id))
        }, duration)
      }
    },
    []
  )

  const confirmToast = useCallback(
    (message: string, onConfirm: () => void, confirmLabel = 'Delete') => {
      const id = Math.random().toString(36).substring(2, 10)
      const dismiss = () => removeToast(id)
      setToasts((prev) => [
        ...prev,
        {
          id,
          message,
          variant: 'warning',
          duration: 0,
          actions: [
            {
              label: confirmLabel,
              variant: 'confirm',
              onClick: () => {
                dismiss()
                onConfirm()
              },
            },
            { label: 'Cancel', variant: 'cancel', onClick: dismiss },
          ],
        },
      ])
    },
    [removeToast]
  )

  const value = useMemo(
    () => ({ toasts, addToast, confirmToast, removeToast }),
    [toasts, addToast, confirmToast, removeToast]
  )

  return (
    <ToastContext.Provider value={value}>
      {children}

      {/* Toast container */}
      <div className="pointer-events-none fixed bottom-4 right-4 z-50 flex flex-col gap-2">
        <AnimatePresence>
          {toasts.map((toast) => (
            <motion.div
              key={toast.id}
              initial={{ opacity: 0, y: 20, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 12, scale: 0.95 }}
              transition={{ duration: 0.25, ease: 'easeOut' }}
              className={`pointer-events-auto rounded-lg border px-4 py-3 shadow-lg ${
                toast.variant === 'success'
                  ? 'border-emerald-200 bg-emerald-50 text-emerald-900'
                  : toast.variant === 'error'
                    ? 'border-red-200 bg-red-50 text-red-900'
                    : toast.variant === 'warning'
                      ? 'border-amber-200 bg-amber-50 text-amber-900'
                      : 'border-outline-variant bg-surface-container-low text-on-surface'
              }`}
            >
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm font-medium">{toast.message}</p>
                {!toast.actions && (
                  <button
                    onClick={() => removeToast(toast.id)}
                    className="shrink-0 text-current opacity-50 hover:opacity-100"
                  >
                    &times;
                  </button>
                )}
              </div>
              {toast.actions && (
                <div className="mt-2 flex items-center justify-end gap-2">
                  {toast.actions.map((action) => (
                    <button
                      key={action.label}
                      onClick={action.onClick}
                      className={`rounded px-3 py-1 text-xs font-bold transition-all ${
                        action.variant === 'confirm'
                          ? 'bg-red-600 text-white hover:bg-red-700'
                          : 'bg-surface-container-high text-on-surface-variant hover:bg-surface-container-highest'
                      }`}
                    >
                      {action.label}
                    </button>
                  ))}
                </div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  )
}
