import { Link } from 'react-router'
import { ReactNode } from 'react'

interface EmptyStateProps {
  /** Kórinis ikonkası: tekst/emoji qatarı (sol qalpında kórsetiledi) yamasa lucide ikonkası sıyaqlı element. */
  icon: ReactNode
  title: string
  message: string
  ctaText: string
  ctaLink?: string
  onClick?: () => void
  /** Bul pútkil ekran bolsa (mısalı "kiriw kerek") 1, sonda bette óziniń bir h1 i qaladı */
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
