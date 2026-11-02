import { SocialButton } from '../components/SocialButton'
import { profile } from '../data/profile'
import { useI18n } from '../i18n/context'

export function Contact() {
  const { t } = useI18n()
  return (
    <section id="contact" className="section" aria-labelledby="contact-title">
      <h2 id="contact-title">{t('contact.title')}</h2>
      <p className="lead">{t('contact.body')}</p>
      <div className="socials">
        {profile.socials.map((link) => (
          <SocialButton key={link.id} link={link} />
        ))}
      </div>
    </section>
  )
}
