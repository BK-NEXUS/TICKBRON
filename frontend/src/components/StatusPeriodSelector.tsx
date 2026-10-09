import { textKeys, useI18n, useTexts } from '../i18n/I18nContext'
import { useId, useState } from 'react'
import { STATUS_PRESET_PERIODS, validateCustomRange, type DateRange } from '../utils/statusPeriod'

interface StatusPeriodSelectorProps {
  /** 'all' | a preset | 'custom' | 'YYYY' | 'YYYY-MM' */
  value: string
  onChange: (period: string) => void
  /** The applied custom range (value "custom") */
  range?: DateRange | null
  /** Passing this handler turns on the custom range option */
  onRangeChange?: (range: DateRange) => void
  /** For tests; defaults to now */
  today?: Date
}

const TEXT_KEYS = textKeys({
  period: 'status.period',
  year: 'status.year',
  month: 'status.month',
  from: 'status.from',
  to: 'status.to',
  apply: 'partner.apply',
  all: 'status.all',
  aYear: 'status.aYear',
  aMonth: 'status.aMonth',
  custom: 'status.custom',

})
const YEARS_BACK = 5
const PRESETS = STATUS_PRESET_PERIODS.map(preset => preset.value as string)

function modeOf(value: string): string {
  if (value === 'all' || value === 'custom' || PRESETS.includes(value)) return value
  return value.length === 4 ? 'year' : 'month'
}

/** Period filter for the Status sections: all time, a preset, a year, a month or a custom range */
export function StatusPeriodSelector({ value, onChange, range, onRangeChange, today = new Date() }: StatusPeriodSelectorProps) {
  const TEXT = useTexts(TEXT_KEYS)
  const i18n = useI18n()
  const { t, formatDate } = i18n
  const id = useId()
  const [customChosen, setCustomChosen] = useState(false)
  const [from, setFrom] = useState(range?.from ?? '')
  const [to, setTo] = useState(range?.to ?? '')
  const [rangeError, setRangeError] = useState<string | null>(null)

  const currentYear = today.getFullYear()
  const mode = customChosen ? 'custom' : modeOf(value)
  const hasYear = mode === 'year' || mode === 'month'
  const year = hasYear ? Number(value.slice(0, 4)) : currentYear
  const month = mode === 'month' ? value.slice(5, 7) : String(today.getMonth() + 1).padStart(2, '0')

  const years = Array.from({ length: YEARS_BACK + 1 }, (_, i) => currentYear - i)
  if (!years.includes(year)) years.push(year)

  const handleMode = (next: string) => {
    setCustomChosen(next === 'custom')
    setRangeError(null)
    if (next === 'custom') return
    if (next === 'year') onChange(String(year))
    else if (next === 'month') onChange(`${year}-${month}`)
    else onChange(next)
  }

  const applyRange = () => {
    const message = validateCustomRange(from, to, i18n)
    setRangeError(message)
    if (message) return
    setCustomChosen(false)
    onRangeChange?.({ from, to })
  }

  return (
    <div className="status-period-selector">
      <label htmlFor={`${id}-mode`}>{TEXT.period}</label>
      <select id={`${id}-mode`} value={mode} onChange={e => handleMode(e.target.value)}>
        <option value="all">{TEXT.all}</option>
        {STATUS_PRESET_PERIODS.map(preset => <option key={preset.value} value={preset.value}>{t(preset.labelKey)}</option>)}
        <option value="year">{TEXT.aYear}</option>
        <option value="month">{TEXT.aMonth}</option>
        {onRangeChange && <option value="custom">{TEXT.custom}</option>}
      </select>
      {hasYear && (
        <>
          <label htmlFor={`${id}-year`} className="sr-only">{TEXT.year}</label>
          <select
            id={`${id}-year`}
            value={String(year)}
            onChange={e => onChange(mode === 'year' ? e.target.value : `${e.target.value}-${month}`)}
          >
            {years.map(y => <option key={y} value={y}>{y}</option>)}
          </select>
        </>
      )}
      {mode === 'month' && (
        <>
          <label htmlFor={`${id}-month`} className="sr-only">{TEXT.month}</label>
          <select id={`${id}-month`} value={month} onChange={e => onChange(`${year}-${e.target.value}`)}>
            {Array.from({ length: 12 }, (_, index) => {
              const number = String(index + 1).padStart(2, '0')
              return <option key={number} value={number}>{formatDate(new Date(2024, index, 1), { month: 'long' })}</option>
            })}
          </select>
        </>
      )}
      {mode === 'custom' && (
        <div className="status-custom-range">
          <label htmlFor={`${id}-from`}>{TEXT.from}</label>
          <input
            id={`${id}-from`} type="date" value={from} onChange={e => setFrom(e.target.value)}
            aria-invalid={rangeError ? true : undefined} aria-describedby={rangeError ? `${id}-error` : undefined}
          />
          <label htmlFor={`${id}-to`}>{TEXT.to}</label>
          <input
            id={`${id}-to`} type="date" value={to} onChange={e => setTo(e.target.value)}
            aria-invalid={rangeError ? true : undefined} aria-describedby={rangeError ? `${id}-error` : undefined}
          />
          <button type="button" className="btn btn-secondary" onClick={applyRange}>{TEXT.apply}</button>
          {rangeError && <p id={`${id}-error`} role="alert" className="status-range-error">{rangeError}</p>}
        </div>
      )}
    </div>
  )
}
