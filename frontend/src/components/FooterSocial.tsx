import { useEffect, useId, useRef, useState } from 'react'
import { Send } from 'lucide-react'
import { useI18n } from '../i18n/I18nContext'
import { SOCIAL_LINKS } from '../utils/socialLinks'

const EXTERNAL = { target: '_blank', rel: 'noopener noreferrer' } as const

/** lucide-react has no brand icons, so Instagram's round logo (its own colours) is drawn here. */
function InstagramLogo({ size, id }: { size: number; id: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 40 40" aria-hidden="true" focusable="false">
      <defs>
        <linearGradient id={id} x1="4" y1="36" x2="36" y2="4" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#FEDA75" />
          <stop offset="0.25" stopColor="#FA7E1E" />
          <stop offset="0.5" stopColor="#D62976" />
          <stop offset="0.75" stopColor="#962FBF" />
          <stop offset="1" stopColor="#4F5BD5" />
        </linearGradient>
      </defs>
      <circle cx="20" cy="20" r="20" fill={`url(#${id})`} />
      <rect x="11.5" y="11.5" width="17" height="17" rx="5" fill="none" stroke="#fff" strokeWidth="2" />
      <circle cx="20" cy="20" r="4" fill="none" stroke="#fff" strokeWidth="2" />
      <circle cx="25.2" cy="14.8" r="1.1" fill="#fff" />
    </svg>
  )
}

export function BrandInstagramLink() {
  const { t } = useI18n()
  const gradientId = useId()
  return (
    <a className="footer-instagram" href={SOCIAL_LINKS.tickbronInstagram} aria-label={t('footer.instagram')}
      title={t('footer.instagram')} {...EXTERNAL}>
      <InstagramLogo size={44} id={gradientId} />
    </a>
  )
}

/** A small "Developer" entry among the Legal links: opens a card with the developer's Telegram and Instagram. */
export function DeveloperContacts() {
  const { t } = useI18n()
  const [open, setOpen] = useState(false)
  const root = useRef<HTMLLIElement>(null)
  const menuId = useId()
  const gradientId = useId()

  useEffect(() => {
    if (!open) return
    const onKey = (event: KeyboardEvent) => { if (event.key === 'Escape') setOpen(false) }
    const onPointer = (event: MouseEvent) => {
      if (root.current && !root.current.contains(event.target as Node)) setOpen(false)
    }
    document.addEventListener('keydown', onKey)
    document.addEventListener('mousedown', onPointer)
    return () => {
      document.removeEventListener('keydown', onKey)
      document.removeEventListener('mousedown', onPointer)
    }
  }, [open])

  return (
    <li className="footer-developer" ref={root}>
      <button type="button" className="footer-link-button" aria-expanded={open} aria-controls={menuId}
        aria-label={t('footer.developerContacts')} onClick={() => setOpen(value => !value)}>
        {t('footer.developer')}
      </button>
      {open && (
        <ul className="footer-developer-menu" id={menuId}>
          <li>
            <a href={SOCIAL_LINKS.developerTelegram} {...EXTERNAL}><Send size={16} aria-hidden="true" />Telegram</a>
          </li>
          <li>
            <a href={SOCIAL_LINKS.developerInstagram} {...EXTERNAL}><InstagramLogo size={16} id={gradientId} />Instagram</a>
          </li>
        </ul>
      )}
    </li>
  )
}
