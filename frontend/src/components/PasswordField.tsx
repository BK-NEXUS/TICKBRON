import { useEffect, useId, useState } from 'react'
import type { ChangeEvent, KeyboardEvent } from 'react'
import { Eye, EyeOff } from 'lucide-react'
import { Button } from './Button'
import { useI18n } from '../i18n/I18nContext'

// A shown password is hidden again after this long, in case the screen is left unattended
const AUTO_HIDE_MS = 30_000

interface PasswordFieldProps {
  id: string
  name?: string
  value: string
  onChange: (event: ChangeEvent<HTMLInputElement>) => void
  autoComplete: 'current-password' | 'new-password'
  showLabel?: string
  hideLabel?: string
  required?: boolean
  disabled?: boolean
  minLength?: number
}

/** Password input with a show/hide toggle and a Caps Lock hint. The visible label stays in the form. */
export function PasswordField({ showLabel, hideLabel, ...inputProps }: PasswordFieldProps) {
  const { t } = useI18n()
  const [visible, setVisible] = useState(false)
  const [capsLockOn, setCapsLockOn] = useState(false)
  const hintId = useId()

  useEffect(() => {
    if (!visible) return
    const timer = setTimeout(() => setVisible(false), AUTO_HIDE_MS)
    return () => clearTimeout(timer)
  }, [visible])

  const trackCapsLock = (event: KeyboardEvent<HTMLInputElement>) => {
    setCapsLockOn(event.getModifierState('CapsLock'))
  }

  return (
    <>
      <div className="auth-password-field">
        <input
          {...inputProps}
          type={visible ? 'text' : 'password'}
          className="auth-input"
          aria-describedby={capsLockOn ? hintId : undefined}
          onKeyDown={trackCapsLock}
          onKeyUp={trackCapsLock}
          onBlur={() => setCapsLockOn(false)}
        />
        <Button
          iconOnly
          variant="ghost"
          size="sm"
          className="auth-password-toggle"
          icon={visible ? <EyeOff size={18} /> : <Eye size={18} />}
          aria-label={visible ? (hideLabel ?? t('auth.hidePassword')) : (showLabel ?? t('auth.showPassword'))}
          aria-pressed={visible}
          disabled={inputProps.disabled}
          onClick={() => setVisible(current => !current)}
        />
      </div>
      {capsLockOn && <p id={hintId} className="auth-hint auth-caps-hint" role="status">{t('auth.capsLockOn')}</p>}
    </>
  )
}
