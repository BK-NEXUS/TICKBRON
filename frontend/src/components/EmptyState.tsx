import { Link } from 'react-router-dom'
import { Icon } from './Icon'
import { getIcon, type IconName } from './icons'

interface EmptyStateProps {
  icon: IconName
  title: string
  message: string
  ctaText: string
  ctaLink?: string
  onClick?: () => void
}

export function EmptyState({ icon, title, message, ctaText, ctaLink, onClick }: EmptyStateProps) {
  return (
    <div className="empty-state" role="status" aria-live="polite">
      <div className="empty-state-icon" aria-hidden="true"><Icon icon={getIcon(icon)} size={48} /></div>
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
