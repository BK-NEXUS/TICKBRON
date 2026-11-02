import { profile } from '../data/profile'
import { useI18n } from '../i18n/context'

export function Hero() {
  const { t } = useI18n()
  return (
    <section className="hero" aria-labelledby="hero-title">
      <p className="eyebrow">{t('hero.role')}</p>
      <h1 id="hero-title">
        {profile.firstName} <span className="accent">{profile.lastName}</span>
      </h1>
      <a className="button" href="#certificates">
        {t('hero.cta')}
      </a>
    </section>
  )
}
