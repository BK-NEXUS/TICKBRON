import { describe, it, expect, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ChargeMain, ChargeNotes } from './ChargeAmount'
import { I18nProvider } from '../i18n/I18nContext'

const USD_BOOKING = {
  total_price: 200,
  currency: 'USD',
  charge_amount: '2354590.00',
  charge_currency: 'UZS',
  exchange_rate: { rate: '11772.950000', date: '2026-10-09', source: 'cbu.uz', stale: false },
}

function renderBoth(booking: Parameters<typeof ChargeMain>[0]['booking']) {
  return render(
    <I18nProvider>
      <p data-testid="main"><ChargeMain booking={booking} /></p>
      <div data-testid="notes"><ChargeNotes booking={booking} /></div>
    </I18nProvider>,
  )
}

describe('ChargeMain and ChargeNotes', () => {
  afterEach(() => localStorage.clear())

  it('shows the so\'m charge as the main number and the hotel price after a sign', () => {
    renderBoth(USD_BOOKING)
    expect(screen.getByTestId('main')).toHaveTextContent('2 354 590')
    expect(screen.getByTestId('main')).toHaveTextContent('UZS')
    expect(screen.getByTestId('notes')).toHaveTextContent('≈ $200')
  })

  it('names the rate date', () => {
    renderBoth(USD_BOOKING)
    expect(screen.getByTestId('notes')).toHaveTextContent('Rate of Oct 9, 2026 (CBU)')
  })

  it('warns when the rate may be out of date', () => {
    renderBoth({ ...USD_BOOKING, exchange_rate: { ...USD_BOOKING.exchange_rate, stale: true } })
    expect(screen.getByTestId('notes')).toHaveTextContent('The rate may be out of date')
  })

  it('has no stale warning for a fresh rate', () => {
    renderBoth(USD_BOOKING)
    expect(screen.getByTestId('notes')).not.toHaveTextContent('out of date')
  })

  it('shows no approximate price and no rate for a booking already in so\'m', () => {
    renderBoth({
      total_price: 450000, currency: 'UZS', charge_amount: '450000.00', charge_currency: 'UZS',
      exchange_rate: { rate: '1.000000', date: null, source: 'identity', stale: false },
    })
    expect(screen.getByTestId('main')).toHaveTextContent('450 000')
    expect(screen.getByTestId('notes')).toBeEmptyDOMElement()
  })

  it('shows an old booking (no charge fields) as it is: its own price, no notes', () => {
    renderBoth({ total_price: 500, currency: 'USD' })
    expect(screen.getByTestId('main')).toHaveTextContent('$500')
    expect(screen.getByTestId('notes')).toBeEmptyDOMElement()
  })

  it('omits the rate line when the rate has no date', () => {
    renderBoth({ ...USD_BOOKING, exchange_rate: { rate: '11772.95', date: null, source: 'demo', stale: false } })
    expect(screen.getByTestId('notes')).toHaveTextContent('≈ $200')
    expect(screen.getByTestId('notes')).not.toHaveTextContent('Rate of')
  })

  it('is written in Uzbek and Russian', () => {
    localStorage.setItem('tickbron.language', 'uz')
    const uz = renderBoth(USD_BOOKING)
    expect(screen.getByTestId('notes')).toHaveTextContent('dagi kurs (MB)')
    uz.unmount()
    localStorage.setItem('tickbron.language', 'ru')
    renderBoth(USD_BOOKING)
    expect(screen.getByTestId('notes')).toHaveTextContent('Курс на')
    expect(screen.getByTestId('notes')).toHaveTextContent('(ЦБ)')
  })
})
