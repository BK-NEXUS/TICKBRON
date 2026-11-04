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
        <ul className="cert-list" aria-label={t('certs.title')}>
          {certificates.map((cert) => (
            <li key={cert.id} className="cert-row">
              <p className="cert-score">{cert.score}</p>
              <div className="cert-body">
                <p className="cert-name">{cert.name}</p>
                <p className="cert-issuer">{cert.issuer}</p>
              </div>
              <p className="cert-year">{cert.year}</p>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
