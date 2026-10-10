import { Link } from 'react-router-dom'
import { ReactNode } from 'react'

interface EmptyStateProps {
  /** Visual icon: a text/emoji string (rendered as-is) or an element such as a lucide icon. */
  icon: ReactNode
  title: string
  message: string
  ctaText: string
  ctaLink?: string
  onClick?: () => void
  /** 1 when this is the whole screen (e.g. "sign in required"), so the page still has its one h1 */
  headingLevel?: 1 | 2
}

export function EmptyState({ icon, title, message, ctaText, ctaLink, onClick, headingLevel = 2 }: EmptyStateProps) {
  const Heading = headingLevel === 1 ? 'h1' : 'h2'
  return (
    <div className="empty-state" role="status" aria-live="polite">
      <div className="empty-state-icon" aria-hidden="true">{icon}</div>
      <Heading className="empty-state-title">{title}</Heading>
      <p className="empty-state-message">{message}</p>
      {ctaLink ? (
        <Link to={ctaLink} className="btn btn-primary empty-state-cta">
          {ctaText}
        </Link>
      ) : onClick ? (
        <button onClick={onClick} className="btn btn-primary empty-state-cta">
          {ctaText}
        </button>
      ) : null}
    </div>
  )
}
