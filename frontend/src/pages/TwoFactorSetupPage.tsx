import { useEffect, useRef, useState } from 'react'
import { Navigate, useNavigate } from 'react-router'
import { authAdapter } from '../adapters/authAdapter'
import { BrandLogo } from '../components/BrandLogo'
import { Button } from '../components/Button'
import { QrCode } from '../components/QrCode'
import { useAuth } from '../contexts/AuthContext'
import { useI18n } from '../i18n/I18nContext'
import { saveBlob } from '../utils/saveBlob'

type Step = { name: 'starting' } | { name: 'failed'; error: string }
  | { name: 'scan'; uri: string; secret: string } | { name: 'codes'; codes: string[] }

/** One-time setup of the authenticator app. Administrators are sent here until it is done. */
export function TwoFactorSetupPage() {
  const { t } = useI18n()
  const { user, isLoading, refreshUser, logout } = useAuth()
  const navigate = useNavigate()
  const [step, setStep] = useState<Step>({ name: 'starting' })
  const [code, setCode] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [copied, setCopied] = useState(false)
  const [saved, setSaved] = useState(false)
  // Every call to setup makes a new secret, so the page asks once even when React runs the effect twice
  const asked = useRef(false)

  const start = async () => {
    setStep({ name: 'starting' })
    const response = await authAdapter.startTwoFactorSetup()
    setStep(response.success && response.otpauthUri && response.secret
      ? { name: 'scan', uri: response.otpauthUri, secret: response.secret }
      : { name: 'failed', error: response.error || t('twoFactorSetup.startError') })
  }

  const signedIn = Boolean(user)
  const alreadyOn = Boolean(user?.two_factor_enabled)
  useEffect(() => {
    if (!signedIn || alreadyOn || asked.current) return
    asked.current = true
    void start()
  // start() only reads `t` for an error text; the effect must run once per visit
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [signedIn, alreadyOn])

  if (isLoading) return <div className="page-loader">{t('common.loading')}</div>
  if (!user) return <Navigate to="/login" replace />
  // Once it is on, only the backup-code screen keeps the page open
  if (user.two_factor_enabled && step.name !== 'codes') return <Navigate to="/" replace />

  const confirm = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!code.trim()) {
      setError(t('twoFactorSetup.codeRequired'))
      return
    }
    setError('')
    setBusy(true)
    const response = await authAdapter.confirmTwoFactorSetup(code.trim())
    if (response.success && response.backupCodes) {
      setStep({ name: 'codes', codes: response.backupCodes })
      await refreshUser()
    } else {
      setError(response.error || t('twoFactorSetup.startError'))
    }
    setBusy(false)
  }

  const copySecret = async (secret: string) => {
    try {
      await navigator.clipboard.writeText(secret)
      setCopied(true)
    } catch {
      setCopied(false)
    }
  }

  const downloadCodes = (codes: string[]) =>
    saveBlob(new Blob([`${codes.join('\n')}\n`], { type: 'text/plain' }), 'tickbron-backup-codes.txt')

  const finish = () => navigate(user.is_superuser || user.is_staff ? '/admin' : '/', { replace: true })

  return (
    <div className="auth-page">
      <div className="container">
        <BrandLogo variant="auth" />
        <div className="auth-container two-factor-setup">
          <div className="auth-header">
            <h1 className="auth-title">{t('twoFactorSetup.title')}</h1>
            <p className="auth-subtitle">{t('twoFactorSetup.intro')}</p>
          </div>

          {step.name === 'starting' && <p className="loading-state" role="status">{t('twoFactorSetup.starting')}</p>}

          {step.name === 'failed' && (
            <div className="auth-error" role="alert">
              <p>{step.error}</p>
              <Button type="button" variant="secondary" size="sm" onClick={() => void start()}>
                {t('twoFactorSetup.tryAgain')}
              </Button>
            </div>
          )}

          {step.name === 'scan' && (
            <>
              <ol className="two-factor-steps">
                <li>{t('twoFactorSetup.step1')}</li>
                <li>
                  {t('twoFactorSetup.step2')}
                  <QrCode value={step.uri} label={t('twoFactorSetup.qrLabel')} />
                  <p className="auth-hint">{t('twoFactorSetup.manual')}</p>
                  <div className="two-factor-secret">
                    <code>{step.secret}</code>
                    <Button type="button" variant="secondary" size="sm" onClick={() => void copySecret(step.secret)}>
                      {copied ? t('twoFactorSetup.copied') : t('twoFactorSetup.copy')}
                    </Button>
                  </div>
                </li>
                <li>{t('twoFactorSetup.step3')}</li>
              </ol>

              {error && <div className="auth-error" role="alert">{error}</div>}

              <form className="auth-form" onSubmit={confirm} noValidate>
                <div className="auth-field">
                  <label htmlFor="two-factor-confirm" className="auth-label">{t('twoFactorSetup.codeLabel')}</label>
                  <input
                    id="two-factor-confirm"
                    className="auth-input"
                    value={code}
                    onChange={(event) => setCode(event.target.value)}
                    inputMode="numeric"
                    autoComplete="one-time-code"
                    maxLength={7}
                    disabled={busy}
                  />
                </div>
                <Button type="submit" size="lg" fullWidth className="auth-submit" loading={busy} disabled={busy}>
                  {busy ? t('twoFactorSetup.confirming') : t('twoFactorSetup.confirm')}
                </Button>
              </form>
            </>
          )}

          {step.name === 'codes' && (
            <>
              <h2 className="two-factor-codes-title">{t('twoFactorSetup.codesTitle')}</h2>
              <p className="auth-hint">{t('twoFactorSetup.codesHint')}</p>
              <ul className="two-factor-codes">
                {step.codes.map(backupCode => <li key={backupCode}><code>{backupCode}</code></li>)}
              </ul>
              <Button type="button" variant="secondary" onClick={() => downloadCodes(step.codes)}>
                {t('twoFactorSetup.download')}
              </Button>
              <label className="two-factor-saved">
                <input type="checkbox" checked={saved} onChange={(event) => setSaved(event.target.checked)} />
                {t('twoFactorSetup.saved')}
              </label>
              <Button type="button" size="lg" fullWidth className="auth-submit" disabled={!saved} onClick={finish}>
                {t('twoFactorSetup.done')}
              </Button>
            </>
          )}

          {step.name !== 'codes' && (
            <div className="auth-footer">
              <button type="button" className="auth-link auth-link-button" onClick={async () => { await logout(); navigate('/login') }}>
                {t('twoFactorSetup.signOut')}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default TwoFactorSetupPage
