import { PasswordField } from './PasswordField'
import { useI18n } from '../i18n/I18nContext'

interface NewPasswordFieldsProps {
  password: string
  confirmation: string
  onPasswordChange: (value: string) => void
  onConfirmationChange: (value: string) => void
  disabled?: boolean
}

/** A new password typed twice, with the length hint. Used where a password is reset or changed. */
export function NewPasswordFields({
  password,
  confirmation,
  onPasswordChange,
  onConfirmationChange,
  disabled,
}: NewPasswordFieldsProps) {
  const { t } = useI18n()

  return (
    <>
      <div className="auth-field">
        <label htmlFor="new-password" className="auth-label">
          {t('auth.newPassword')}
        </label>
        <PasswordField
          id="new-password"
          value={password}
          onChange={(event) => onPasswordChange(event.target.value)}
          required
          disabled={disabled}
          autoComplete="new-password"
        />
        <p className="auth-hint">{t('auth.passwordHint')}</p>
      </div>

      <div className="auth-field">
        <label htmlFor="new-password-confirm" className="auth-label">
          {t('auth.confirmPassword')}
        </label>
        <PasswordField
          id="new-password-confirm"
          value={confirmation}
          onChange={(event) => onConfirmationChange(event.target.value)}
          required
          disabled={disabled}
          autoComplete="new-password"
          showLabel={t('auth.showConfirmPassword')}
          hideLabel={t('auth.hideConfirmPassword')}
        />
      </div>
    </>
  )
}
