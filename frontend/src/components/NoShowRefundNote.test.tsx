import { describe, it, expect, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { NoShowRefundNote } from './NoShowRefundNote'
import { I18nProvider } from '../i18n/I18nContext'
import type { NoShowRefundInfo } from '../adapters/noShowAdapter'

const FIFTY: NoShowRefundInfo = {
  no_show_refund_percent: 50,
  no_show_refund_amount: '450000.00',
  no_show_refund_text_key: 'no_show_refund_statement',
  no_show_refund_text_params: { percent: 50, amount: '450000.00' },
}

function renderNote(info: NoShowRefundInfo | null | undefined) {
  return render(
    <I18nProvider>
      <NoShowRefundNote info={info} />
    </I18nProvider>,
  )
}

describe('NoShowRefundNote', () => {
  afterEach(() => localStorage.clear())

  it('shows the 50% sentence with the exact amount the backend sent, in English', () => {
    renderNote(FIFTY)
    const note = screen.getByTestId('no-show-refund-note')
    expect(note).toHaveTextContent('If you do not arrive and this is confirmed, 50% of your payment (450')
    expect(note).toHaveTextContent('UZS')
  })

  it('is written in Uzbek', () => {
    localStorage.setItem('tickbron.language', 'uz')
    renderNote(FIFTY)
    expect(screen.getByTestId('no-show-refund-note')).toHaveTextContent("Agar siz kelmasangiz va bu tasdiqlansa, to'lovning 50% i")
  })

  it('is written in Russian', () => {
    localStorage.setItem('tickbron.language', 'ru')
    renderNote(FIFTY)
    expect(screen.getByTestId('no-show-refund-note')).toHaveTextContent('Если вы не приедете и это будет подтверждено, вернём 50% платежа')
  })

  it('uses the percent-only sentence when the backend sent no amount (charge not in UZS)', () => {
    renderNote({
      no_show_refund_percent: 50, no_show_refund_amount: null,
      no_show_refund_text_key: 'no_show_refund_statement', no_show_refund_text_params: { percent: 50, amount: null },
    })
    const note = screen.getByTestId('no-show-refund-note')
    expect(note).toHaveTextContent('50% of your payment')
    expect(note).not.toHaveTextContent('null')
  })

  it('shows nothing for an old booking without the refund promise (0%)', () => {
    const { container } = renderNote({
      no_show_refund_percent: 0, no_show_refund_amount: null, no_show_refund_text_key: null, no_show_refund_text_params: null,
    })
    expect(container).toBeEmptyDOMElement()
  })

  it('shows nothing when the data is missing or the text key is unknown', () => {
    expect(renderNote(null).container).toBeEmptyDOMElement()
    expect(renderNote(undefined).container).toBeEmptyDOMElement()
    expect(renderNote({ ...FIFTY, no_show_refund_text_key: 'something_else' }).container).toBeEmptyDOMElement()
    expect(renderNote({ ...FIFTY, no_show_refund_text_params: null }).container).toBeEmptyDOMElement()
  })

  it('never invents an amount: it prints the backend value, not a calculation', () => {
    renderNote({ ...FIFTY, no_show_refund_text_params: { percent: 50, amount: '123456.00' } })
    expect(screen.getByTestId('no-show-refund-note')).toHaveTextContent('123')
  })
})
