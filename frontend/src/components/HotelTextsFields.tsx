import { useI18n } from '../i18n/I18nContext'
import { HOTEL_TEXT_LANGUAGES, type HotelTextLanguage, type HotelTextsForm } from '../utils/hotelTexts'

interface HotelTextsFieldsProps {
  idPrefix: string
  value: HotelTextsForm
  onChange: (value: HotelTextsForm) => void
  disabled?: boolean
}

const LANGUAGE_NAMES: Record<HotelTextLanguage, string> = { uz: 'Oʻzbekcha', ru: 'Русский', en: 'English' }

/** Hotel name and description in uz / ru / en; guests see their own language, else another one. */
export function HotelTextsFields({ idPrefix, value, onChange, disabled = false }: HotelTextsFieldsProps) {
  const { t } = useI18n()

  const set = (language: HotelTextLanguage, field: 'name' | 'description', text: string) =>
    onChange({ ...value, [language]: { ...value[language], [field]: text } })

  return (
    <div className="hotel-texts">
      <p className="form-hint">{t('hotelTexts.hint')}</p>
      {HOTEL_TEXT_LANGUAGES.map(language => (
        <fieldset key={language} className="hotel-texts-language" disabled={disabled}>
          <legend>{LANGUAGE_NAMES[language]}</legend>
          <div className="form-group">
            <label htmlFor={`${idPrefix}-name-${language}`}>{t('hotelTexts.name', { language: LANGUAGE_NAMES[language] })}</label>
            <input
              id={`${idPrefix}-name-${language}`}
              type="text"
              maxLength={255}
              value={value[language].name}
              onChange={(e) => set(language, 'name', e.target.value)}
              className="form-input"
            />
          </div>
          <div className="form-group">
            <label htmlFor={`${idPrefix}-description-${language}`}>{t('hotelTexts.description', { language: LANGUAGE_NAMES[language] })}</label>
            <textarea
              id={`${idPrefix}-description-${language}`}
              rows={3}
              maxLength={2000}
              value={value[language].description}
              onChange={(e) => set(language, 'description', e.target.value)}
              className="form-input"
            />
          </div>
        </fieldset>
      ))}
    </div>
  )
}
