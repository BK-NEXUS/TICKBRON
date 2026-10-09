import { useI18n } from '../i18n/I18nContext'
import { Link } from 'react-router-dom'

export function NotFoundPage() {
  const { t } = useI18n()
  return (
    <div className="not-found-page">
      <div className="container">
        <h1>404</h1>
        <h2>{t('notFound.title')}</h2>
        <p>{t('notFound.text')}</p>
        <Link to="/" className="btn btn-primary">{t('common.goHome')}</Link>
      </div>
    </div>
  )
}

export default NotFoundPage
