import { useId } from 'react'

interface StatusPeriodSelectorProps {
  /** 'all' | 'YYYY' | 'YYYY-MM' */
  value: string
  onChange: (period: string) => void
  /** For tests; defaults to now */
  today?: Date
}

const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August',
  'September', 'October', 'November', 'December']
const YEARS_BACK = 5

/** Period filter for the Status sections: all time, a year, or a month */
export function StatusPeriodSelector({ value, onChange, today = new Date() }: StatusPeriodSelectorProps) {
  const id = useId()
  const currentYear = today.getFullYear()
  const mode = value === 'all' ? 'all' : value.length === 4 ? 'year' : 'month'
  const year = mode === 'all' ? currentYear : Number(value.slice(0, 4))
  const month = mode === 'month' ? value.slice(5, 7) : String(today.getMonth() + 1).padStart(2, '0')

  const years = Array.from({ length: YEARS_BACK + 1 }, (_, i) => currentYear - i)
  if (!years.includes(year)) years.push(year)

  const handleMode = (next: string) => {
    if (next === 'all') onChange('all')
    else if (next === 'year') onChange(String(year))
    else onChange(`${year}-${month}`)
  }

  return (
    <div className="status-period-selector">
      <label htmlFor={`${id}-mode`}>Period</label>
      <select id={`${id}-mode`} value={mode} onChange={e => handleMode(e.target.value)}>
        <option value="all">All time</option>
        <option value="year">A year</option>
        <option value="month">A month</option>
      </select>
      {mode !== 'all' && (
        <>
          <label htmlFor={`${id}-year`} className="sr-only">Year</label>
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
          <label htmlFor={`${id}-month`} className="sr-only">Month</label>
          <select id={`${id}-month`} value={month} onChange={e => onChange(`${year}-${e.target.value}`)}>
            {MONTHS.map((name, index) => {
              const number = String(index + 1).padStart(2, '0')
              return <option key={number} value={number}>{name}</option>
            })}
          </select>
        </>
      )}
    </div>
  )
}
