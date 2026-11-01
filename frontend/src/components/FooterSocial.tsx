import { useEffect, useId, useRef, useState } from 'react'
import { Code2, Send } from 'lucide-react'
import { useI18n } from '../i18n/I18nContext'
import { SOCIAL_LINKS } from '../utils/socialLinks'

const EXTERNAL = { target: '_blank', rel: 'noopener noreferrer' } as const

/** lucide-react has no brand icons, so the Instagram glyph is drawn here. */
function InstagramIcon({ size = 18 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
      strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">
      <rect x="3" y="3" width="18" height="18" rx="5" />
      <circle cx="12" cy="12" r="4" />
      <circle cx="17.5" cy="6.5" r="0.6" fill="currentColor" />
    </svg>
  )
}

export function BrandInstagramLink() {
  const { t } = useI18n()
  return (
    <a className="footer-social-link" href={SOCIAL_LINKS.tickbronInstagram} aria-label={t('footer.instagram')}
      title={t('footer.instagram')} {...EXTERNAL}>
      <InstagramIcon />
    </a>
  )
}

/** "Developer" pill: opens a small card with the developer's Telegram and Instagram. */
export function DeveloperContacts() {
  const { t } = useI18n()
  const [open, setOpen] = useState(false)
  const root = useRef<HTMLDivElement>(null)
  const menuId = useId()

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
    <div className="footer-developer" ref={root}>
      <button type="button" className="footer-developer-button" aria-expanded={open} aria-controls={menuId}
        aria-label={t('footer.developerContacts')} onClick={() => setOpen(value => !value)}>
        <Code2 size={16} aria-hidden="true" />
        <span>{t('footer.developer')}</span>
      </button>
      {open && (
        <ul className="footer-developer-menu" id={menuId}>
          <li>
            <a href={SOCIAL_LINKS.developerTelegram} {...EXTERNAL}><Send size={16} aria-hidden="true" />Telegram</a>
          </li>
          <li>
            <a href={SOCIAL_LINKS.developerInstagram} {...EXTERNAL}><InstagramIcon size={16} />Instagram</a>
          </li>
        </ul>
      )}
    </div>
  )
}
