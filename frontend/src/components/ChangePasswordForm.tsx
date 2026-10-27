import { useState } from 'react'
import { authAdapter } from '../adapters/authAdapter'
import { Button } from './Button'
import { NewPasswordFields } from './NewPasswordFields'
import { PasswordField } from './PasswordField'
import { useI18n } from '../i18n/I18nContext'
import { formAccepts } from '../utils/formProblem'
import { newPasswordProblem } from '../utils/passwordRules'

/** Change the password of the signed-in account. The current password is asked for again. */
export function ChangePasswordForm() {
  const { t } = useI18n()
  const [currentPassword, setCurrentPassword] = useState('')
  const [password, setPassword] = useState('')
  const [confirmation, setConfirmation] = useState('')
  const [error, setError] = useState('')
  const [changed, setChanged] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError('')
    setChanged(false)
    if (!formAccepts(event.currentTarget, t, setError)) return

    const problem = newPasswordProblem(password, confirmation)
    if (problem) {
      setError(t(problem === 'mismatch' ? 'auth.errorPasswordMismatch' : 'auth.errorPasswordShort'))
      return
    }

    setIsLoading(true)
    const response = await authAdapter.changePassword({
      current_password: currentPassword,
      password,
      password_confirm: confirmation,
    })
    setIsLoading(false)

    if (response.success) {
      setChanged(true)
      setCurrentPassword('')
      setPassword('')
      setConfirmation('')
    } else {
      setError(response.error || t('profile.errorChangePassword'))
    }
  }

  return (
    <div className="profile-section">
      <h2 className="profile-section-title">{t('profile.changePassword')}</h2>
      <form className="auth-form" onSubmit={handleSubmit} noValidate>
        {error && (
          <div className="auth-error" role="alert">
            {error}
          </div>
        )}
        {changed && (
          <div className="auth-notice" role="status">
            {t('profile.passwordChanged')}
          </div>
        )}

        <div className="auth-field">
          <label htmlFor="current-password" className="auth-label">
            {t('profile.currentPassword')}
          </label>
          <PasswordField
            id="current-password"
            value={currentPassword}
            onChange={(event) => setCurrentPassword(event.target.value)}
            required
            disabled={isLoading}
            autoComplete="current-password"
          />
        </div>

        <NewPasswordFields
          password={password}
          confirmation={confirmation}
          onPasswordChange={setPassword}
          onConfirmationChange={setConfirmation}
          disabled={isLoading}
        />

        <Button type="submit" loading={isLoading} disabled={isLoading}>
          {isLoading ? t('auth.savingPassword') : t('profile.changePassword')}
        </Button>
      </form>
    </div>
  )
}
