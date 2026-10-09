import { useState } from 'react'
import type { ChangeEvent } from 'react'
import { Eye, EyeOff } from 'lucide-react'
import { Button } from './Button'
import { useI18n } from '../i18n/I18nContext'

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

/** Password input with a show/hide toggle. The visible label stays in the form. */
export function PasswordField({ showLabel, hideLabel, ...inputProps }: PasswordFieldProps) {
  const { t } = useI18n()
  const [visible, setVisible] = useState(false)

  return (
    <div className="auth-password-field">
      <input {...inputProps} type={visible ? 'text' : 'password'} className="auth-input" />
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
  )
}
