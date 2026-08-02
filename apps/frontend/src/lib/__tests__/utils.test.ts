import { describe, expect, it } from 'vitest'

import { cn, formatBytes, formatDate, formatDateTime, generateId, truncate } from '@/lib/utils'

describe('cn', () => {
  it('merges conflicting Tailwind classes with twMerge', () => {
    expect(cn('px-2', 'px-4')).toBe('px-4')
  })

  it('drops falsy values via clsx', () => {
    expect(cn('text-red-500', false, null, undefined, 'bg-blue-500')).toBe(
      'text-red-500 bg-blue-500'
    )
  })
})

describe('formatDate', () => {
  it('formats a Date object with default options', () => {
    expect(formatDate(new Date('2025-01-15'))).toBe('Jan 15, 2025')
  })

  it('accepts an ISO string', () => {
    expect(formatDate('2025-01-15')).toBe('Jan 15, 2025')
  })

  it('respects custom Intl options', () => {
    expect(
      formatDate(new Date('2025-01-15'), { year: 'numeric', month: '2-digit', day: '2-digit' })
    ).toBe('01/15/2025')
  })
})

describe('formatDateTime', () => {
  it('includes time in the output', () => {
    expect(formatDateTime(new Date('2025-01-15T10:30:00'))).toContain('Jan 15, 2025')
    expect(formatDateTime(new Date('2025-01-15T10:30:00'))).toMatch(/10:30 (AM|PM)/)
  })
})

describe('truncate', () => {
  it('returns the string unchanged when short enough', () => {
    expect(truncate('hi', 5)).toBe('hi')
  })

  it('truncates with an ellipsis and trims trailing whitespace', () => {
    expect(truncate('hello world', 5)).toBe('hello...')
    expect(truncate('hello   world', 5)).toBe('hello...')
  })
})

describe('formatBytes', () => {
  it('handles zero', () => {
    expect(formatBytes(0)).toBe('0 Bytes')
  })

  it('formats KiB/MiB/GiB units', () => {
    expect(formatBytes(1024)).toBe('1 KB')
    expect(formatBytes(1536)).toBe('1.5 KB')
    expect(formatBytes(1024 ** 2)).toBe('1 MB')
    expect(formatBytes(1024 ** 3)).toBe('1 GB')
  })

  it('respects the decimals argument', () => {
    expect(formatBytes(5_000_000, 0)).toBe('5 MB')
    expect(formatBytes(5_000_000, 2)).toBe('4.77 MB')
  })
})

describe('generateId', () => {
  it('returns a non-empty alphanumeric string', () => {
    const id = generateId()
    expect(typeof id).toBe('string')
    expect(id.length).toBeGreaterThan(0)
    expect(id).toMatch(/^[a-z0-9]+$/)
  })
})
