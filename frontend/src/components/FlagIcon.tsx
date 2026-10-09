import type { Language } from '../i18n/options'

// Inline SVG instead of flag emoji: emoji look different on every platform and Windows shows letters
const FLAGS: Record<Language, JSX.Element> = {
  uz: (
    <>
      <rect width="24" height="16" fill="#1eb53a" />
      <rect width="24" height="10.67" fill="#ffffff" />
      <rect width="24" height="5.33" fill="#0099b5" />
      <rect y="5.33" width="24" height="0.8" fill="#ce1126" />
      <rect y="9.87" width="24" height="0.8" fill="#ce1126" />
      <circle cx="5" cy="2.7" r="1.6" fill="#ffffff" />
      <circle cx="5.6" cy="2.7" r="1.4" fill="#0099b5" />
    </>
  ),
  ru: (
    <>
      <rect width="24" height="16" fill="#ffffff" />
      <rect y="5.33" width="24" height="5.34" fill="#0039a6" />
      <rect y="10.67" width="24" height="5.33" fill="#d52b1e" />
    </>
  ),
  en: (
    <>
      <rect width="24" height="16" fill="#012169" />
      <path d="M0 0 24 16M24 0 0 16" stroke="#ffffff" strokeWidth="3.2" />
      <path d="M0 0 24 16M24 0 0 16" stroke="#c8102e" strokeWidth="1.2" />
      <path d="M12 0v16M0 8h24" stroke="#ffffff" strokeWidth="5.2" />
      <path d="M12 0v16M0 8h24" stroke="#c8102e" strokeWidth="3" />
    </>
  ),
}

export function FlagIcon({ language }: { language: Language }) {
  return (
    <svg className="flag-icon" viewBox="0 0 24 16" width="20" height="14" aria-hidden="true" focusable="false">
      <clipPath id={`flag-clip-${language}`}>
        <rect width="24" height="16" rx="2" />
      </clipPath>
      <g clipPath={`url(#flag-clip-${language})`}>{FLAGS[language]}</g>
    </svg>
  )
}
