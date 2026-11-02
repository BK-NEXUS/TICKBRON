import { profile } from '../data/profile'
import { useI18n } from '../i18n/context'

export function Hero() {
  const { t } = useI18n()
  return (
    <section className="hero" aria-labelledby="hero-title">
      <h1 id="hero-title">
        <span className="line">
          <span>{profile.firstName}</span>
        </span>{' '}
        <span className="line">
          <span>{profile.lastName}</span>
        </span>
      </h1>
      <p className="role">{t('hero.role')}</p>
      <a className="button" href="#certificates">
        {t('hero.cta')}
      </a>
    </section>
  )
}
