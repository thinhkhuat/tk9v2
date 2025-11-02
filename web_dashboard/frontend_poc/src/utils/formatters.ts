/**
 * Utility functions for formatting dates, file sizes, and durations.
 */

/**
 * Format a date as relative time (e.g., "2 hours ago", "3 days ago")
 */
export function formatDate(date: string | Date): string {
  const now = new Date()
  const then = typeof date === 'string' ? new Date(date) : date
  const diffMs = now.getTime() - then.getTime()
  const diffSec = Math.floor(diffMs / 1000)
  const diffMin = Math.floor(diffSec / 60)
  const diffHour = Math.floor(diffMin / 60)
  const diffDay = Math.floor(diffHour / 24)
  const diffWeek = Math.floor(diffDay / 7)
  const diffMonth = Math.floor(diffDay / 30)
  const diffYear = Math.floor(diffDay / 365)

  if (diffSec < 60) {
    return 'just now'
  } else if (diffMin < 60) {
    return `${diffMin} ${diffMin === 1 ? 'minute' : 'minutes'} ago`
  } else if (diffHour < 24) {
    return `${diffHour} ${diffHour === 1 ? 'hour' : 'hours'} ago`
  } else if (diffDay < 7) {
    return `${diffDay} ${diffDay === 1 ? 'day' : 'days'} ago`
  } else if (diffWeek < 4) {
    return `${diffWeek} ${diffWeek === 1 ? 'week' : 'weeks'} ago`
  } else if (diffMonth < 12) {
    return `${diffMonth} ${diffMonth === 1 ? 'month' : 'months'} ago`
  } else {
    return `${diffYear} ${diffYear === 1 ? 'year' : 'years'} ago`
  }
}

/**
 * Format a date as absolute date/time (e.g., "Jan 15, 2025 at 3:45 PM")
 */
export function formatAbsoluteDate(date: string | Date): string {
  const dateObj = typeof date === 'string' ? new Date(date) : date

  const options: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true
  }

  return dateObj.toLocaleDateString('en-US', options).replace(',', ' at')
}

/**
 * Format file size in human-readable format (e.g., "1.5 MB", "243 KB")
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes'

  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))

  const value = bytes / Math.pow(k, i)
  const decimals = i === 0 ? 0 : 2 // No decimals for bytes

  return `${value.toFixed(decimals)} ${sizes[i]}`
}

/**
 * Format duration in human-readable format (e.g., "2h 30m", "45s")
 */
export function formatDuration(seconds: number): string {
  if (seconds < 60) {
    return `${Math.floor(seconds)}s`
  }

  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)

  const parts = []
  if (hours > 0) parts.push(`${hours}h`)
  if (minutes > 0) parts.push(`${minutes}m`)
  if (secs > 0 && hours === 0) parts.push(`${secs}s`) // Only show seconds if under an hour

  return parts.join(' ')
}

/**
 * Format duration between two dates
 */
export function formatDurationBetween(start: string | Date, end: string | Date): string {
  const startDate = typeof start === 'string' ? new Date(start) : start
  const endDate = typeof end === 'string' ? new Date(end) : end
  const diffMs = endDate.getTime() - startDate.getTime()
  const diffSec = diffMs / 1000

  return formatDuration(diffSec)
}

/**
 * Format a number with thousands separators (e.g., "1,234,567")
 */
export function formatNumber(num: number): string {
  return num.toLocaleString('en-US')
}

/**
 * Get status badge color classes for Tailwind CSS
 */
export function getStatusColor(status: string): string {
  const statusColors: Record<string, string> = {
    'in_progress': 'bg-blue-100 text-blue-800',
    'completed': 'bg-green-100 text-green-800',
    'failed': 'bg-red-100 text-red-800',
    'pending': 'bg-gray-100 text-gray-800'
  }

  return statusColors[status] || 'bg-gray-100 text-gray-800'
}

/**
 * Get language badge color classes for Tailwind CSS
 */
export function getLanguageColor(language: string | undefined | null): string {
  const languageColors: Record<string, string> = {
    'vi': 'bg-blue-100 text-blue-800',
    'en': 'bg-green-100 text-green-800',
    'es': 'bg-yellow-100 text-yellow-800',
    'fr': 'bg-purple-100 text-purple-800',
    'de': 'bg-red-100 text-red-800',
    'ja': 'bg-pink-100 text-pink-800',
    'zh': 'bg-orange-100 text-orange-800'
  }

  if (!language) return 'bg-gray-100 text-gray-800'
  return languageColors[language.toLowerCase()] || 'bg-gray-100 text-gray-800'
}

/**
 * Truncate text to a maximum length with ellipsis
 */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength - 3) + '...'
}
