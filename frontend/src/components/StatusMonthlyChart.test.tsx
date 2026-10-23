import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { StatusMonthlyChart } from './StatusMonthlyChart'
import { I18nProvider } from '../i18n/I18nContext'
import type { StatusMonth } from '../adapters/statusAdapter'

const month = (n: number, guests: number, usd: string | null): StatusMonth => ({
  month: `2026-${String(n).padStart(2, '0')}`, bookings: guests, guests, nights: 0, stayed: 0,
  revenue: usd ? [{ currency: 'USD', amount: usd }] : [],
}) as StatusMonth

function renderChart(metric: 'guests' | 'revenue') {
  localStorage.setItem('tickbron.language', 'en')
  return render(
    <I18nProvider>
      <StatusMonthlyChart months={[month(1, 34, '54201950.00'), month(2, 0, null)]} year={2026} metric={metric} currency="USD" />
    </I18nProvider>,
  )
}

describe('StatusMonthlyChart', () => {
  it('revenue bars carry a short label and the whole amount in the title', () => {
    const { container } = renderChart('revenue')

    const bar = container.querySelector('.bar') as HTMLElement
    expect(bar.querySelector('.bar-label')).toHaveTextContent('$54.2M')
    expect(bar).toHaveAttribute('title', '$54,201,950.00')
    expect(screen.getByRole('img', { name: 'Revenue (USD) per month in 2026' })).toBeInTheDocument()
  })

  it('a month without revenue has no label', () => {
    const { container } = renderChart('revenue')
    expect(container.querySelectorAll('.bar-label')).toHaveLength(1)
  })

  it('guest bars show the count', () => {
    const { container } = renderChart('guests')
    expect(container.querySelector('.bar-label')).toHaveTextContent('34')
  })
})
