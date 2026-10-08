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
}

export function EmptyState({ icon, title, message, ctaText, ctaLink, onClick }: EmptyStateProps) {
  return (
    <div className="empty-state" role="status" aria-live="polite">
      <div className="empty-state-icon" aria-hidden="true">{icon}</div>
      <h2 className="empty-state-title">{title}</h2>
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
