import type { MouseEvent } from 'react'
import { useI18n } from '../i18n/context'
import { useTheme } from '../theme/context'

export function ThemeToggle() {
  const { t } = useI18n()
  const { theme, toggle } = useTheme()

  const onClick = (e: MouseEvent<HTMLButtonElement>) => {
    const box = e.currentTarget.getBoundingClientRect()
    toggle({ x: box.left + box.width / 2, y: box.top + box.height / 2 })
  }

  return (
    <button type="button" className="theme-toggle" onClick={onClick} aria-label={t(theme === 'dark' ? 'theme.toLight' : 'theme.toDark')}>
      <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
        {theme === 'dark' ? (
          <path fill="currentColor" d="M12 4a1 1 0 0 1 1 1v1a1 1 0 1 1-2 0V5a1 1 0 0 1 1-1Zm0 14a1 1 0 0 1 1 1v1a1 1 0 1 1-2 0v-1a1 1 0 0 1 1-1Zm8-7a1 1 0 1 1 0 2h-1a1 1 0 1 1 0-2h1ZM6 12a1 1 0 1 1 0 2H5a1 1 0 1 1 0-2h1Zm10.2-5.8a1 1 0 0 1 0 1.4l-.7.7a1 1 0 1 1-1.4-1.4l.7-.7a1 1 0 0 1 1.4 0ZM9.9 14.1a1 1 0 0 1 0 1.4l-.7.7a1 1 0 1 1-1.4-1.4l.7-.7a1 1 0 0 1 1.4 0Zm6.3 2.1a1 1 0 0 1-1.4 1.4l-.7-.7a1 1 0 1 1 1.4-1.4l.7.7ZM9.9 9.9a1 1 0 0 1-1.4 0l-.7-.7a1 1 0 0 1 1.4-1.4l.7.7a1 1 0 0 1 0 1.4ZM12 8a4 4 0 1 1 0 8 4 4 0 0 1 0-8Z" />
        ) : (
          <path fill="currentColor" d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5Z" />
        )}
      </svg>
    </button>
  )
}
