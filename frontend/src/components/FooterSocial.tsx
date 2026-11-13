import { useEffect, useId, useRef, useState } from 'react'
import { Send } from 'lucide-react'
import { useI18n } from '../i18n/I18nContext'
import { SOCIAL_LINKS } from '../utils/socialLinks'

const EXTERNAL = { target: '_blank', rel: 'noopener noreferrer' } as const

/** React tiń useId() ı belgiler (mısalı «») alıp júriwi múmkin, olar ayırım brauzerlerde url(#id) siltemelerin buzadı. */
function useSvgId() {
  return `ig-${useId().replace(/[^A-Za-z0-9_-]/g, '')}`
}

/** lucide-react te brend ikonkaları joq, sol sebepli Instagram logotipi (jumalaq kvadrat, óz gradienti) usı jerde sızıladı. */
function InstagramLogo({ size, id }: { size: number; id: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 40 40" aria-hidden="true" focusable="false">
      <defs>
        <radialGradient id={id} cx="12" cy="43" r="46" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#FDF497" />
          <stop offset="0.05" stopColor="#FDF497" />
          <stop offset="0.45" stopColor="#FD5949" />
          <stop offset="0.6" stopColor="#D6249F" />
          <stop offset="0.9" stopColor="#285AEB" />
        </radialGradient>
      </defs>
      <rect width="40" height="40" rx="10" fill={`url(#${id})`} />
      <rect x="10.5" y="10.5" width="19" height="19" rx="5.5" fill="none" stroke="#fff" strokeWidth="2.2" />
      <circle cx="20" cy="20" r="4.5" fill="none" stroke="#fff" strokeWidth="2.2" />
      <circle cx="25.6" cy="14.4" r="1.3" fill="#fff" />
    </svg>
  )
}

export function BrandInstagramLink() {
  const { t } = useI18n()
  const gradientId = useSvgId()
  return (
    <a className="footer-instagram" href={SOCIAL_LINKS.tickbronInstagram} aria-label={t('footer.instagram')}
      title={t('footer.instagram')} {...EXTERNAL}>
      <InstagramLogo size={52} id={gradientId} />
    </a>
  )
}

/** Huquqıy siltemeler arasında kishi "Developer" jazbası: programmistiń Telegram hám Instagram ı bar kartanı ashadı. */
export function DeveloperContacts() {
  const { t } = useI18n()
  const [open, setOpen] = useState(false)
  const root = useRef<HTMLLIElement>(null)
  const menuId = useId()
  const gradientId = useSvgId()

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
