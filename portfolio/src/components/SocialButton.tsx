import { useI18n } from '../i18n/context'
import type { SocialLink } from '../data/profile'

const ICONS: Record<SocialLink['id'], string> = {
  telegram: 'M21.5 3.5 2.8 10.7c-1.3.5-1.2 1.2-.2 1.5l4.8 1.5 1.8 5.6c.2.6.1.8.7.8.5 0 .7-.2 1-.5l2.3-2.2 4.8 3.5c.9.5 1.5.2 1.7-.8l3-14.3c.3-1.2-.5-1.8-1.4-1.3ZM8.2 13.4l9.9-6.2c.5-.3.9-.1.5.2l-8.2 7.4-.3 3.4-1.9-4.8Z',
  instagram: 'M7 2h10a5 5 0 0 1 5 5v10a5 5 0 0 1-5 5H7a5 5 0 0 1-5-5V7a5 5 0 0 1 5-5Zm0 2a3 3 0 0 0-3 3v10a3 3 0 0 0 3 3h10a3 3 0 0 0 3-3V7a3 3 0 0 0-3-3H7Zm5 3.5a4.5 4.5 0 1 1 0 9 4.5 4.5 0 0 1 0-9Zm0 2a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5Zm5.2-3.2a1 1 0 1 1 0 2 1 1 0 0 1 0-2Z',
  linkedin: 'M4.5 3a2 2 0 1 1 0 4 2 2 0 0 1 0-4ZM3 9h3v12H3V9Zm6 0h2.9v1.7c.5-.9 1.7-2 3.6-2 3.4 0 4 2.2 4 5.1V21h-3v-6.2c0-1.5 0-3.3-2-3.3s-2.5 1.5-2.5 3.2V21H9V9Z',
  email: 'M3 5h18a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1Zm1 2.5V17h16V7.5l-8 5.5-8-5.5ZM5.5 7 12 11.5 18.5 7h-13Z',
}

export function SocialButton({ link }: { link: SocialLink }) {
  const { t } = useI18n()
  const external = link.href.startsWith('https://')
  return (
    <a
      className="social-button"
      href={link.href}
      {...(external ? { target: '_blank', rel: 'noopener noreferrer' } : {})}
      aria-label={external ? `${link.label} (${t('a11y.external')})` : link.label}
    >
      <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
        <path d={ICONS[link.id]} fill="currentColor" />
      </svg>
      <span>{link.label}</span>
    </a>
  )
}
