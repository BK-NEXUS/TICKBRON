import { useNavigate } from 'react-router-dom'
import { SegmentedControl, type SegmentedOption } from './SegmentedControl'
import { useI18n } from '../i18n/I18nContext'

type AuthMode = 'login' | 'register'

const ROUTES: Record<AuthMode, string> = { login: '/login', register: '/register' }

/** Switches between the sign-in and the create-account page. */
export function AuthModeSwitch({ mode, disabled }: { mode: AuthMode; disabled?: boolean }) {
  const navigate = useNavigate()
  const { t } = useI18n()
  const options: SegmentedOption<AuthMode>[] = [
    { value: 'login', label: t('auth.logIn') },
    { value: 'register', label: t('auth.register') },
  ]
  return (
    <SegmentedControl<AuthMode>
      mode="tabs"
      fullWidth
      disabled={disabled}
      aria-label={t('auth.account')}
      options={options}
      value={mode}
      onChange={next => next !== mode && navigate(ROUTES[next])}
    />
  )
}
