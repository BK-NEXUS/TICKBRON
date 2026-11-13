import { useState } from 'react'
import { useI18n } from '../i18n/I18nContext'
import { OTHER_LETTER } from '../utils/alphabet'

const LATIN = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('')
// Rus alfaviti hám ózbek Kirillinin tórt qosımsha háripi
const CYRILLIC = 'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯЎҚҒҲ'.split('')

type Script = 'latin' | 'cyrillic'

interface AlphabetFilterProps {
  /** Tańlanǵan háripi, háripten baslanbaytuǵın atlar ushın '#', yamasa hámmesi ushın '' */
  value: string
  onChange: (letter: string) => void
  disabled?: boolean
}

/**
 * Adamlar yamasa mehmanxanalar dizimin háripten baslanatuǵın atlarǵa shekemlewshi A-Z (yamasa Kirill háripleri) túymeleri.
 * Dizim filterlewdi serverde isleydi; bul tek qaysı háripti aytadı. Jazıw bet tiline ılayıq
 * (rus tilinde Kirill kórsetiledi) hám almastırıw múmkin, sebebi atlar eki jazıwda da jazıladı.
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
