import { BrandLogo } from './BrandLogo'
import { useI18n } from '../i18n/I18nContext'

export function Footer() {
  const { t } = useI18n()
  return (
    <footer className="footer">
      <div className="container footer-container">
        <div className="footer-section">
          <BrandLogo variant="footer" decorative />
          <h3>TICKBRON</h3>
          <p>{t('footer.tagline')}</p>
        </div>
        <div className="footer-section">
          <h4>{t('footer.explore')}</h4>
          <ul>
            <li><a href="/search">{t('nav.properties')}</a></li>
            <li><a href="/destinations">{t('footer.destinations')}</a></li>
          </ul>
        </div>
        <div className="footer-section">
          <h4>{t('footer.support')}</h4>
          <ul>
            <li><a href="/help">{t('footer.helpCenter')}</a></li>
            <li><a href="/contact">{t('footer.contact')}</a></li>
            <li><a href="/safety">{t('footer.safety')}</a></li>
          </ul>
        </div>
        <div className="footer-section">
          <h4>{t('footer.legal')}</h4>
          <ul>
            <li><a href="/terms">{t('footer.terms')}</a></li>
            <li><a href="/privacy">{t('footer.privacy')}</a></li>
            <li><a href="/cookies">{t('footer.cookies')}</a></li>
          </ul>
        </div>
      </div>
      <div className="container footer-bottom">
        <p>{t('footer.rights', { year: new Date().getFullYear() })}</p>
      </div>
    </footer>
  )
}
