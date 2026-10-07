import { useId } from 'react'
import type { StatusGranularity } from '../adapters/statusAdapter'

interface StatusGranularitySelectorProps {
  value: StatusGranularity
  onChange: (granularity: StatusGranularity) => void
}

const TEXT = {
  label: 'Group by',
  options: [
    { value: 'day', label: 'Day' },
    { value: 'week', label: 'Week' },
    { value: 'month', label: 'Month' },
    { value: 'year', label: 'Year' },
  ] as { value: StatusGranularity; label: string }[],
}

/** Bucket size of the Status series chart */
export function StatusGranularitySelector({ value, onChange }: StatusGranularitySelectorProps) {
  const id = useId()
  return (
    <div className="status-field">
      <label htmlFor={id}>{TEXT.label}</label>
      <select id={id} value={value} onChange={e => onChange(e.target.value as StatusGranularity)}>
        {TEXT.options.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}
      </select>
    </div>
  )
}
