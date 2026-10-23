import { useId, useState } from 'react'
import { useI18n } from '../i18n/I18nContext'
import type { StatusMonth } from '../adapters/statusAdapter'
import { chartCurrencies } from '../utils/statusFormat'
import { StatusMonthlyChart } from './StatusMonthlyChart'

interface StatusYearChartsProps {
  months: StatusMonth[]
  year: number
  availableYears: number[]
  onYearChange: (year: number) => void
}

/** The year selector, the revenue chart (one currency at a time) and the guests chart. */
export function StatusYearCharts({ months, year, availableYears, onYearChange }: StatusYearChartsProps) {
  const { t } = useI18n()
  const id = useId()
  const [currency, setCurrency] = useState<string | null>(null)
  const years = availableYears.includes(year) ? availableYears : [...availableYears, year].sort()
  const currencies = chartCurrencies(months)
  const chartCurrency = currency && currencies.includes(currency) ? currency : currencies[0]

  return (
    <section aria-labelledby={`${id}-title`}>
      <h3 id={`${id}-title`} className="status-chart-title">{t('status.yearTitle')}</h3>
      <div className="status-controls">
        <div className="status-field">
          <label htmlFor={`${id}-year`}>{t('status.chartYear')}</label>
          <select id={`${id}-year`} value={year} onChange={e => onYearChange(Number(e.target.value))}>
            {years.map(y => <option key={y} value={y}>{y}</option>)}
          </select>
        </div>
        {currencies.length > 1 && (
          <div className="status-field">
            <label htmlFor={`${id}-currency`}>{t('status.chartCurrency')}</label>
            <select id={`${id}-currency`} value={chartCurrency} onChange={e => setCurrency(e.target.value)}>
              {currencies.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
        )}
      </div>
      <div className="status-charts">
        {chartCurrency ? (
          <StatusMonthlyChart months={months} year={year} metric="revenue" currency={chartCurrency} />
        ) : (
          <div className="empty-state"><p>{t('status.noRevenueIn', { year })}</p></div>
        )}
        <StatusMonthlyChart months={months} year={year} metric="guests" />
      </div>
    </section>
  )
}
