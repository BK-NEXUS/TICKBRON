import { useState } from 'react'
import { useI18n } from '../i18n/I18nContext'
import { OTHER_LETTER } from '../utils/alphabet'

const LATIN = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('')
// The Russian alphabet and the four extra letters of Uzbek Cyrillic
const CYRILLIC = 'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯЎҚҒҲ'.split('')

type Script = 'latin' | 'cyrillic'

interface AlphabetFilterProps {
  /** The chosen letter, '#' for names that do not start with a letter, or '' for everything */
  value: string
  onChange: (letter: string) => void
  disabled?: boolean
}

/**
 * Buttons A-Z (or the Cyrillic letters) that narrow a list of people or hotels to the names starting with a letter.
 * The list does the filtering on the server; this only says which letter. The script follows the page language
 * (Russian shows Cyrillic) and can be switched, because names are written in both.
 */
export function AlphabetFilter({ value, onChange, disabled = false }: AlphabetFilterProps) {
  const { t, language } = useI18n()
  const [script, setScript] = useState<Script>(() => (language === 'ru' || /[А-ЯЎҚҒҲ]/.test(value) ? 'cyrillic' : 'latin'))
  const letters = script === 'latin' ? LATIN : CYRILLIC

  return (
    <nav className="alphabet-filter" aria-label={t('alphabet.label')}>
      <button type="button" className={`alphabet-button${value === '' ? ' alphabet-button--active' : ''}`}
        aria-pressed={value === ''} disabled={disabled} onClick={() => onChange('')}>
        {t('alphabet.all')}
      </button>
      {letters.map(letter => (
        <button key={letter} type="button" className={`alphabet-button${value === letter ? ' alphabet-button--active' : ''}`}
          aria-pressed={value === letter} aria-label={t('alphabet.letterLabel', { letter })} disabled={disabled}
          onClick={() => onChange(value === letter ? '' : letter)}>
          {letter}
        </button>
      ))}
      <button type="button" className={`alphabet-button${value === OTHER_LETTER ? ' alphabet-button--active' : ''}`}
        aria-pressed={value === OTHER_LETTER} aria-label={t('alphabet.otherLabel')} disabled={disabled}
        onClick={() => onChange(value === OTHER_LETTER ? '' : OTHER_LETTER)}>
        {OTHER_LETTER}
      </button>
      <button type="button" className="alphabet-button alphabet-button--script" disabled={disabled}
        onClick={() => setScript(previous => (previous === 'latin' ? 'cyrillic' : 'latin'))}>
        {t(script === 'latin' ? 'alphabet.toCyrillic' : 'alphabet.toLatin')}
      </button>
    </nav>
  )
}
