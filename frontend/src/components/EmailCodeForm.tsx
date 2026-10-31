import { useEffect, useState } from 'react'
import { Button } from './Button'
import { useI18n } from '../i18n/I18nContext'
import type { AuthResponse } from '../adapters/authAdapter'

const CODE_LENGTH = 6

interface EmailCodeFormProps {
  /** "o***@gmail.com" or the full address: where the code went */
  sentTo: string
  /** Sign-up or sign-in: picks the words and the button */
  purpose: 'register' | 'login'
  /** Seconds before a new code may be asked for (the answer that started this step says it) */
  resendAfter: number
  onSubmit: (code: string) => Promise<AuthResponse>
  onResend: () => Promise<AuthResponse>
  onSuccess: () => void
  onBack: () => void
}

const digitsOnly = (value: string) => value.replace(/\D/g, '').slice(0, CODE_LENGTH)

/** The step after the password: the six digits mailed to the address, with "send a new code" after a short wait. */
export function EmailCodeForm({ sentTo, purpose, resendAfter, onSubmit, onResend, onSuccess, onBack }: EmailCodeFormProps) {
  const { t } = useI18n()
  const [value, setValue] = useState('')
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [busy, setBusy] = useState(false)
  const [secondsLeft, setSecondsLeft] = useState(resendAfter)

  useEffect(() => {
    if (secondsLeft <= 0) return undefined
    const timer = setTimeout(() => setSecondsLeft(previous => previous - 1), 1000)
    return () => clearTimeout(timer)
  }, [secondsLeft])

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    if (value.length !== CODE_LENGTH) {
      setError(t('auth.emailCodeInvalid'))
      return
    }
    setError('')
    setNotice('')
    setBusy(true)
    const response = await onSubmit(value)
    setBusy(false)
    if (response.success) onSuccess()
    else setError(response.error || t('auth.emailCodeWrong'))
  }

  const handleResend = async () => {
    setError('')
    setNotice('')
    setBusy(true)
    const response = await onResend()
    setBusy(false)
    if (response.success) {
      setValue('')
      setNotice(t('auth.emailCodeResent'))
      setSecondsLeft(response.resendAfter ?? resendAfter)
    } else {
      setError(response.error || t('auth.emailCodeResendFailed'))
    }
  }

  return (
    <>
      <div className="auth-header">
        <h1 className="auth-title">{t('auth.emailCodeTitle')}</h1>
        <p className="auth-subtitle">{t(purpose === 'register' ? 'auth.emailCodeSubtitleRegister' : 'auth.emailCodeSubtitleLogin', { email: sentTo })}</p>
      </div>

      {error && <div className="auth-error" role="alert">{error}</div>}
      {notice && <div className="auth-hint" role="status">{notice}</div>}

      <form className="auth-form" onSubmit={handleSubmit} noValidate>
        <div className="auth-field">
          <label htmlFor="email-code" className="auth-label">{t('auth.emailCodeLabel')}</label>
          <input
            id="email-code"
            className="auth-input"
            value={value}
            onChange={(event) => setValue(digitsOnly(event.target.value))}
            inputMode="numeric"
            pattern="[0-9]*"
            autoComplete="one-time-code"
            spellCheck={false}
            maxLength={CODE_LENGTH}
            disabled={busy}
            autoFocus
          />
          <p className="auth-hint">{t('auth.emailCodeSpam')}</p>
        </div>

        <Button type="submit" size="lg" fullWidth className="auth-submit" loading={busy} disabled={busy}>
          {t(purpose === 'register' ? 'auth.emailCodeSubmitRegister' : 'auth.emailCodeSubmitLogin')}
        </Button>
      </form>

      <div className="auth-footer auth-footer--stacked">
        <button type="button" className="auth-link auth-link-button" onClick={() => void handleResend()} disabled={busy || secondsLeft > 0}>
          {secondsLeft > 0 ? t('auth.emailCodeResendIn', { seconds: secondsLeft }) : t('auth.emailCodeResend')}
        </button>
        <button type="button" className="auth-link auth-link-button" onClick={onBack} disabled={busy}>
          {t('auth.emailCodeBack')}
        </button>
      </div>
    </>
  )
}
