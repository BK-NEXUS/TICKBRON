import { TiltCard } from '../components/TiltCard'
import type { Certificate } from '../data/profile'
import { useI18n } from '../i18n/context'

export function Certificates({ certificates }: { certificates: Certificate[] }) {
  const { t } = useI18n()
  return (
    <section id="certificates" className="section" aria-labelledby="certs-title">
      <h2 id="certs-title">{t('certs.title')}</h2>
      {certificates.length === 0 ? (
        <p className="lead">{t('certs.empty')}</p>
      ) : (
        <ul className="cert-grid" aria-label={t('certs.title')}>
          {certificates.map((cert) => (
            <li key={cert.id}>
              <TiltCard className="glass cert-card">
                <p className="cert-score">{cert.score}</p>
                <p className="cert-name">{cert.name}</p>
                <p className="cert-meta">
                  {cert.issuer} · {cert.year}
                </p>
              </TiltCard>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
