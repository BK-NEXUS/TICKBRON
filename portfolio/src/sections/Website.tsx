import { TiltCard } from '../components/TiltCard'
import { profile } from '../data/profile'
import { useI18n } from '../i18n/context'

export function Website() {
  const { t } = useI18n()
  return (
    <section id="website" className="section" aria-labelledby="website-title">
      <TiltCard className="glass website-card">
        <h2 id="website-title">{t('website.title')}</h2>
        <p className="lead">{t('website.body')}</p>
        <a className="button" href={profile.website.url} target="_blank" rel="noopener noreferrer">
          {t('website.cta')} · {profile.website.label}
          <span className="sr-only"> ({t('a11y.external')})</span>
        </a>
      </TiltCard>
    </section>
  )
}
