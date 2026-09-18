import { Link } from 'react-router-dom'

interface EmptyStateProps {
  icon: string
  title: string
  message: string
  ctaText: string
  ctaLink: string
}

export function EmptyState({ icon, title, message, ctaText, ctaLink }: EmptyStateProps) {
  return (
    <div className="empty-state" role="status" aria-live="polite">
      <div className="empty-state-icon" aria-hidden="true">{icon}</div>
      <h2 className="empty-state-title">{title}</h2>
      <p className="empty-state-message">{message}</p>
      <Link to={ctaLink} className="btn btn-primary empty-state-cta">
        {ctaText}
      </Link>
    </div>
  )
}
