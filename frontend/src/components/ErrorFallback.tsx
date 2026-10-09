import { useI18n } from '../i18n/I18nContext'

export function ErrorFallback() {
  const { t } = useI18n()
  return (
    <div className="error-fallback">
      <h1 className="error-fallback-title">{t('error.title')}</h1>
      <p className="error-fallback-text">{t('error.text')}</p>
      <button onClick={() => window.location.reload()} className="btn btn-primary">
        {t('error.refresh')}
      </button>
    </div>
  )
}
