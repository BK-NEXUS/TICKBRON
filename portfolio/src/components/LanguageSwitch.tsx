import { LANGS } from '../i18n/dictionaries'
import { useI18n } from '../i18n/context'

export function LanguageSwitch() {
  const { lang, setLang, t } = useI18n()
  return (
    <div className="lang-switch" role="group" aria-label={t('lang.label')}>
      {LANGS.map((code) => (
        <button key={code} type="button" aria-pressed={lang === code} onClick={() => setLang(code)}>
          {code.toUpperCase()}
        </button>
      ))}
    </div>
  )
}
