import { useState } from 'react'
import { Button } from './Button'
import { useAuth } from '../contexts/AuthContext'
import { useI18n } from '../i18n/I18nContext'

interface TwoFactorCodeFormProps {
  onSuccess: () => void
  onBack: () => void
}

/** Second step of the sign-in: the app's 6 digits, or a backup code when the phone is not at hand. */
export function TwoFactorCodeForm({ onSuccess, onBack }: TwoFactorCodeFormProps) {
  const { t } = useI18n()
  const { loginTwoFactor } = useAuth()
  const [useBackup, setUseBackup] = useState(false)
  const [value, setValue] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const switchMode = () => {
    setUseBackup(previous => !previous)
    setValue('')
    setError('')
  }

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    const entered = value.trim()
    if (!entered) {
      setError(t('auth.twoFactorRequired'))
      return
    }
    setError('')
    setBusy(true)
    const response = await loginTwoFactor(useBackup ? { backupCode: entered } : { code: entered })
    setBusy(false)
    if (response.success) onSuccess()
    else setError(response.error || t('auth.errorLogin'))
  }

  return (
    <>
      <div className="auth-header">
        <h1 className="auth-title">{t('auth.twoFactorTitle')}</h1>
        <p className="auth-subtitle">{t(useBackup ? 'auth.twoFactorBackupSubtitle' : 'auth.twoFactorSubtitle')}</p>
      </div>

      {error && <div className="auth-error" role="alert">{error}</div>}

      <form className="auth-form" onSubmit={handleSubmit} noValidate>
        <div className="auth-field">
          <label htmlFor="two-factor-code" className="auth-label">
            {t(useBackup ? 'auth.twoFactorBackupLabel' : 'auth.twoFactorCode')}
          </label>
          <input
            id="two-factor-code"
            className="auth-input"
            value={value}
            onChange={(event) => setValue(event.target.value)}
            inputMode={useBackup ? 'text' : 'numeric'}
            autoComplete="one-time-code"
            autoCapitalize="none"
            spellCheck={false}
            maxLength={useBackup ? 12 : 7}
            disabled={busy}
            autoFocus
          />
        </div>

        <Button type="submit" size="lg" fullWidth className="auth-submit" loading={busy} disabled={busy}>
          {busy ? t('auth.twoFactorVerifying') : t('auth.twoFactorSubmit')}
        </Button>
      </form>

      <div className="auth-footer auth-footer--stacked">
        <button type="button" className="auth-link auth-link-button" onClick={switchMode} disabled={busy}>
          {t(useBackup ? 'auth.twoFactorUseApp' : 'auth.twoFactorUseBackup')}
        </button>
        <button type="button" className="auth-link auth-link-button" onClick={onBack} disabled={busy}>
          {t('auth.twoFactorBack')}
        </button>
      </div>
    </>
  )
}
