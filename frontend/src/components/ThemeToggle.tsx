import { Moon, Sun } from 'lucide-react'
import { useTheme } from '../theme/ThemeContext'
import { useI18n } from '../i18n/I18nContext'

export function ThemeToggle({ className = '' }: { className?: string }) {
  const { effectiveTheme, setTheme } = useTheme()
  const { t } = useI18n()
  const isDark = effectiveTheme === 'dark'

  return (
    <button
      type="button"
      className={`btn btn-ghost btn-icon theme-toggle ${className}`.trim()}
      aria-label={isDark ? t('theme.toLight') : t('theme.toDark')}
      aria-pressed={isDark}
      onClick={() => setTheme(isDark ? 'light' : 'dark')}
    >
      {isDark ? <Sun size={18} aria-hidden="true" /> : <Moon size={18} aria-hidden="true" />}
    </button>
  )
}
