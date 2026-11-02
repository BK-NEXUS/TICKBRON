import { Counter } from '../components/Counter'
import { profile } from '../data/profile'
import { useI18n } from '../i18n/context'

export function About() {
  const { t } = useI18n()
  return (
    <section id="about" className="section" aria-labelledby="about-title">
      <h2 id="about-title">{t('about.title')}</h2>
      <p className="lead">{t('about.body')}</p>
      <dl className="stats">
        {profile.stats.map((stat) => (
          <div key={stat.id} className="stat glass">
            <dt>{t(`stats.${stat.id}`)}</dt>
            <dd>
              <Counter value={stat.value} />
            </dd>
          </div>
        ))}
      </dl>
    </section>
  )
}
