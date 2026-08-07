/**
 * Format an ISO timestamp into a compact, human-readable relative time.
 *
 * Returns "just now", "Nm/Nh/Nd ago", or an absolute date for older values.
 * Never returns `Invalid Date` — falls back to "—" on a null/unparseable input
 * (so feeds never render a broken timestamp).
 */
export function formatRelativeTime(iso: string | null | undefined): string {
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return '—'
  const diffSec = Math.round((Date.now() - d.getTime()) / 1000)
  if (diffSec < 60) return 'just now'
  if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`
  if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`
  if (diffSec < 604800) return `${Math.floor(diffSec / 86400)}d ago`
  return d.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}
