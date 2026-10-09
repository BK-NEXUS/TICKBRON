import { textKeys, useTexts } from '../i18n/I18nContext'
import { useId } from 'react'
import type { StatusGranularity } from '../adapters/statusAdapter'

interface StatusGranularitySelectorProps {
  value: StatusGranularity
  onChange: (granularity: StatusGranularity) => void
}

const TEXT_KEYS = textKeys({
  label: 'status.label',
  day: 'status.day',
  week: 'status.week',
  month: 'status.month',
  year: 'status.year',
})

const GRANULARITIES: StatusGranularity[] = ['day', 'week', 'month', 'year']

/** Bucket size of the Status series chart */
export function StatusGranularitySelector({ value, onChange }: StatusGranularitySelectorProps) {
  const TEXT = useTexts(TEXT_KEYS)
  const id = useId()
  return (
    <div className="status-field">
      <label htmlFor={id}>{TEXT.label}</label>
      <select id={id} value={value} onChange={e => onChange(e.target.value as StatusGranularity)}>
        {GRANULARITIES.map(option => <option key={option} value={option}>{TEXT[option]}</option>)}
      </select>
    </div>
  )
}
