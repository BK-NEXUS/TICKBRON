import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { PriceApprox } from './PriceApprox'
import { I18nProvider } from '../i18n/I18nContext'

const rate = { rate: '11772.950000', date: '2026-10-03', source: 'cbu.uz', stale: false }

function renderApprox(props: React.ComponentProps<typeof PriceApprox>, language = 'en') {
  localStorage.setItem('tickbron.language', language)
  return render(<I18nProvider><PriceApprox {...props} /></I18nProvider>)
}

describe('PriceApprox', () => {
  beforeEach(() => localStorage.clear())

  it('shows the equivalent in so\'m (written UZS in English) of a hotel priced in dollars after a ≈', () => {
    const { container } = renderApprox({ approx: '1177295.00' })
    expect(container).toHaveTextContent('≈ 1 177 295 UZS')
  })

  it('writes the unit in the page language', () => {
    const { container } = renderApprox({ approx: '1177295.00' }, 'ru')
    expect(container).toHaveTextContent('≈ 1 177 295 сум')
  })

  it('shows nothing while there is no rate yet, or for a hotel priced in so\'m', () => {
    const { container, rerender } = renderApprox({ approx: null })
    expect(container).toBeEmptyDOMElement()
    rerender(<I18nProvider><PriceApprox approx={undefined} /></I18nProvider>)
    expect(container).toBeEmptyDOMElement()
  })

  it('can add the date of the CBU rate', () => {
    renderApprox({ approx: '1177295.00', rate, showRate: true })
    expect(screen.getByText('Rate of Oct 3, 2026 (CBU)')).toBeInTheDocument()
  })

  it('warns when the rate may be out of date', () => {
    renderApprox({ approx: '1177295.00', rate: { ...rate, stale: true }, showRate: true })
    expect(screen.getByText('The rate may be out of date')).toBeInTheDocument()
  })

  it('keeps the date and the warning off a compact price (cards)', () => {
    renderApprox({ approx: '1177295.00', rate: { ...rate, stale: true } })
    expect(screen.queryByText(/Rate of/)).toBeNull()
    expect(screen.queryByText('The rate may be out of date')).toBeNull()
  })
})
