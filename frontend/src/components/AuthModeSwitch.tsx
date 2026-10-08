import { useNavigate } from 'react-router-dom'
import { SegmentedControl, type SegmentedOption } from './SegmentedControl'

type AuthMode = 'login' | 'register'

const ROUTES: Record<AuthMode, string> = { login: '/login', register: '/register' }

const OPTIONS: SegmentedOption<AuthMode>[] = [
  { value: 'login', label: 'Log in' },
  { value: 'register', label: 'Register' },
]

/** Switches between the sign-in and the create-account page. */
export function AuthModeSwitch({ mode, disabled }: { mode: AuthMode; disabled?: boolean }) {
  const navigate = useNavigate()
  return (
    <SegmentedControl<AuthMode>
      mode="tabs"
      fullWidth
      disabled={disabled}
      aria-label="Account"
      options={OPTIONS}
      value={mode}
      onChange={next => next !== mode && navigate(ROUTES[next])}
    />
  )
}
