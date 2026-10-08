import { useState } from 'react'
import type { ChangeEvent } from 'react'
import { Eye, EyeOff } from 'lucide-react'
import { Button } from './Button'

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
export function PasswordField({
  showLabel = 'Show password', hideLabel = 'Hide password', ...inputProps
}: PasswordFieldProps) {
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
        aria-label={visible ? hideLabel : showLabel}
        aria-pressed={visible}
        disabled={inputProps.disabled}
        onClick={() => setVisible(current => !current)}
      />
    </div>
  )
}
