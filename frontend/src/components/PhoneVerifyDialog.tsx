import { useCallback, useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { useI18n } from '../i18n/I18nContext'
import { authAdapter } from '../adapters/authAdapter'
import { DialogModal } from './DialogModal'

type ErrorKey = 'phoneVerify.errSend' | 'phoneVerify.errInvalid' | 'phoneVerify.errGeneric'

interface PhoneVerifyDialogProps {
  phone: string
  onVerified: () => void
  onClose: () => void
}

/** Proves the logged-in user owns their phone number: an SMS code goes to the number on the account. */
export function PhoneVerifyDialog({ phone, onVerified, onClose }: PhoneVerifyDialogProps) {
  const { t } = useI18n()
  const [code, setCode] = useState('')
  const [sending, setSending] = useState(true)
  const [sent, setSent] = useState(false)
  const [checking, setChecking] = useState(false)
  const [testCode, setTestCode] = useState<string | undefined>(undefined)
  const [errorKey, setErrorKey] = useState<ErrorKey | null>(null)
  const requestedOnOpen = useRef(false)

  const sendCode = useCallback(async () => {
    setSending(true)
    setErrorKey(null)
    const response = await authAdapter.requestPhoneVerification()
    setSending(false)
    if (!response.success) {
      setErrorKey('phoneVerify.errSend')
      return
    }
    setSent(true)
    setTestCode(response.otp_code)
  }, [])

  useEffect(() => {
    if (requestedOnOpen.current) return
    requestedOnOpen.current = true
    void sendCode()
  }, [sendCode])

  const canSubmit = sent && /^\d{6}$/.test(code) && !checking

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    if (!canSubmit) return
    setChecking(true)
    setErrorKey(null)
    const response = await authAdapter.confirmPhoneVerification(code)
    setChecking(false)
    if (!response.success) {
      setErrorKey(response.code === 'otp_invalid' ? 'phoneVerify.errInvalid' : 'phoneVerify.errGeneric')
      return
    }
    onVerified()
  }

  return (
    <DialogModal titleId="phone-verify-title" title={t('phoneVerify.title')} onClose={onClose}>
      <p className="modal-subtitle">{t('phoneVerify.intro', { phone })}</p>
      {sending && <p role="status">{t('phoneVerify.sending')}</p>}
      {errorKey && <p className="alert alert-error" role="alert">{t(errorKey)}</p>}
      {sent && (
        <form onSubmit={submit}>
          <div className="form-group">
            <label htmlFor="phone-verify-code">{t('phoneVerify.code')}</label>
            <input
              id="phone-verify-code"
              className="form-control"
              inputMode="numeric"
              autoComplete="one-time-code"
              maxLength={6}
              value={code}
              onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
            />
            {testCode && import.meta.env.MODE !== 'production' && (
              <small className="form-hint">{t('auth.testCode')} <strong>{testCode}</strong></small>
            )}
          </div>
          <div className="modal-actions">
            <button type="submit" className="btn btn-primary" disabled={!canSubmit}>
              {checking ? t('phoneVerify.verifying') : t('phoneVerify.verify')}
            </button>
            <button type="button" className="btn btn-secondary" onClick={() => void sendCode()} disabled={sending || checking}>
              {t('phoneVerify.resend')}
            </button>
            <button type="button" className="btn btn-secondary" onClick={onClose} disabled={checking}>
              {t('phoneVerify.close')}
            </button>
          </div>
        </form>
      )}
      {!sent && !sending && (
        <div className="modal-actions">
          <button type="button" className="btn btn-primary" onClick={() => void sendCode()}>
            {t('phoneVerify.resend')}
          </button>
          <button type="button" className="btn btn-secondary" onClick={onClose}>
            {t('phoneVerify.close')}
          </button>
        </div>
      )}
    </DialogModal>
  )
}
