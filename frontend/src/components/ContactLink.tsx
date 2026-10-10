import type { ReactNode } from 'react'

interface ContactLinkProps {
  /** Null when the typed value is not safe to turn into a link */
  href: string | null
  className: string
  ariaLabel?: string
  /** Plain text shown instead of the link when href is null */
  fallback?: string
  children: ReactNode
}

export function ContactLink({ href, className, ariaLabel, fallback, children }: ContactLinkProps) {
  if (!href) return fallback ? <span>{fallback}</span> : null
  return (
    <a href={href} target="_blank" rel="noopener noreferrer" className={className} aria-label={ariaLabel}>
      {children}
    </a>
  )
}
