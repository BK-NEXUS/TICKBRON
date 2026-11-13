import { Link } from 'react-router'
import type { ReactNode } from 'react'
import { TriangleAlert } from 'lucide-react'
import { useI18n } from '../i18n/I18nContext'

interface ErrorStateProps {
  /** Ne boldı, kelwshi paydalana alatuǵın sózler menen */
  message: string
  /** Ádetde: "Something went wrong" */
  title?: string
  /** Ádetde: eskertiw úshmúyeshligi; lucide ikonkası yamasa qálegen element */
  icon?: ReactNode
  /** Usı shaqıratuǵın "Try Again" túymesin kórsetedi */
  onRetry?: () => void
  /** Shıǵıw jolı, silteme (ctaLink) yamasa túyme (onCta) retinde; ctaLabel teksten kóbirek aytsa, qol jetkiziwge bolatuǵın at */
  ctaText?: string
  ctaLink?: string
  onCta?: () => void
  ctaLabel?: string
  /** Bul pútkil ekran bolsa 1, sonda bette óziniń bir h1 i qaladı */
  headingLevel?: 1 | 2
}

/** EmptyState penen birdey kórinis, qátelik ushın: ikonka, sarlawha, ne boldı hám keyin ne islew kerek. */
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
