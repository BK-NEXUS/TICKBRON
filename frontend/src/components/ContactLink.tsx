import type { ReactNode } from 'react'

interface ContactLinkProps {
  /** Terilgen mánisti siltemege aylandırıw qáwipsiz bolmasa null */
  href: string | null
  className: string
  ariaLabel?: string
  /** href null bolǵanda silteme ornına kórsetiletuǵın ápiwayı tekst */
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
