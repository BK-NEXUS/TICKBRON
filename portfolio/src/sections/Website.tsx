import { profile } from '../data/profile'
import { useI18n } from '../i18n/context'

export function Website() {
  const { t } = useI18n()
  return (
    <section id="website" className="section" aria-labelledby="website-title">
      <h2 id="website-title">{t('website.title')}</h2>
      <p className="lead">{t('website.body')}</p>
      <a className="link-row" href={profile.website.url} target="_blank" rel="noopener noreferrer">
        <span className="link-row-title">{t('website.cta')}</span>
        <span className="link-row-url">{profile.website.label}</span>
        <span className="sr-only">({t('a11y.external')})</span>
      </a>
    </section>
  )
}
