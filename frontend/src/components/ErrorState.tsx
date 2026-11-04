import { Link } from 'react-router'
import type { ReactNode } from 'react'
import { TriangleAlert } from 'lucide-react'
import { useI18n } from '../i18n/I18nContext'

interface ErrorStateProps {
  /** What happened, in words the visitor can use */
  message: string
  /** Default: "Something went wrong" */
  title?: string
  /** Default: a warning triangle; a lucide icon or any element */
  icon?: ReactNode
  /** Shows a "Try Again" button that calls this */
  onRetry?: () => void
  /** A way out, as a link (ctaLink) or a button (onCta); ctaLabel is the accessible name when it says more than the text */
  ctaText?: string
  ctaLink?: string
  onCta?: () => void
  ctaLabel?: string
  /** 1 when this is the whole screen, so the page still has its one h1 */
  headingLevel?: 1 | 2
}

/** The same look as EmptyState, for a failure: an icon, a title, what happened and what to do next. */
export function ErrorState({
  message, title, icon, onRetry, ctaText, ctaLink, onCta, ctaLabel, headingLevel = 2,
}: ErrorStateProps) {
  const { t } = useI18n()
  const Heading = headingLevel === 1 ? 'h1' : 'h2'
  const hasAction = onRetry || ctaText
  return (
    <div className="empty-state error-state" role="alert" aria-live="assertive">
      <div className="empty-state-icon empty-state-icon--error" aria-hidden="true">{icon ?? <TriangleAlert size={40} />}</div>
      <Heading className="empty-state-title">{title ?? t('state.errorTitle')}</Heading>
      <p className="empty-state-message">{message}</p>
      {hasAction && (
        <div className="state-actions">
          {onRetry && <button type="button" className="btn btn-primary" onClick={onRetry}>{t('common.tryAgain')}</button>}
          {ctaText && ctaLink && <Link to={ctaLink} className={`btn ${onRetry ? 'btn-secondary' : 'btn-primary'}`}>{ctaText}</Link>}
          {ctaText && !ctaLink && onCta && (
            <button type="button" className={`btn ${onRetry ? 'btn-secondary' : 'btn-primary'}`} aria-label={ctaLabel} onClick={onCta}>{ctaText}</button>
          )}
        </div>
      )}
    </div>
  )
}
