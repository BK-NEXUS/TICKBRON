import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render } from '@testing-library/react'
import { CancellationNote, PlanCancellationNote } from './CancellationNote'
import { I18nProvider } from '../i18n/I18nContext'

const NOW = new Date('2026-12-10T10:00:00Z')
const LATER = '2026-12-18T00:00:00+05:00'   // 17 Dec 19:00 UTC: ahead of NOW
const EARLIER = '2026-12-05T00:00:00+05:00'  // behind NOW

function renderNote(element: React.ReactElement, language = 'en') {
  localStorage.setItem('tickbron.language', language)
  return render(<I18nProvider>{element}</I18nProvider>)
}

describe('CancellationNote (what a booking or a quote promises)', () => {
  beforeEach(() => { vi.useFakeTimers({ toFake: ['Date'] }); vi.setSystemTime(NOW); localStorage.clear() })
  afterEach(() => vi.useRealTimers())

  it('a free window that is still ahead: the badge with its date and what comes after it', () => {
    const { container } = renderNote(<CancellationNote freeUntil={LATER} percentAfter={50} />)
    expect(container).toHaveTextContent('Free cancellation until')
    expect(container).toHaveTextContent('Dec 18, 12:00 AM')   // shown in Tashkent time, whatever the browser's zone
    expect(container).toHaveTextContent('After that, 50% of your payment is refunded.')
    expect(container.querySelector('.cancellation-note--free')).not.toBeNull()
  })

  it('a free window followed by a non-refundable rest says so', () => {
    const { container } = renderNote(<CancellationNote freeUntil={LATER} percentAfter={0} />)
    expect(container).toHaveTextContent('After that, the booking is non-refundable.')
  })

  it('a free window that has passed is not free cancellation any more: only the percent is told', () => {
    const { container } = renderNote(<CancellationNote freeUntil={EARLIER} percentAfter={50} />)
    expect(container).not.toHaveTextContent('Free cancellation')
    expect(container).toHaveTextContent('If you cancel, 50% of your payment is refunded.')
  })

  it('without a free window the percent applies at any time', () => {
    const { container } = renderNote(<CancellationNote freeUntil={null} percentAfter={30} />)
    expect(container).toHaveTextContent('If you cancel, 30% of your payment is refunded.')
    expect(container.querySelector('.cancellation-note--free')).toBeNull()
  })

  it('zero percent is non-refundable', () => {
    const { container } = renderNote(<CancellationNote freeUntil={null} percentAfter={0} />)
    expect(container).toHaveTextContent('Non-refundable: cancelling does not give a refund.')
  })

  it('speaks the page language', () => {
    const { container } = renderNote(<CancellationNote freeUntil={null} percentAfter={0} />, 'ru')
    expect(container).toHaveTextContent('Невозвратная бронь')
  })
})

describe('PlanCancellationNote (what a rate plan offers, before dates are chosen)', () => {
  beforeEach(() => localStorage.clear())

  it('a plan with a free window shows the badge and how long before the check-in day', () => {
    const { container } = renderNote(<PlanCancellationNote freeCancellation freeCancelHours={48} refundPercent={50} />)
    expect(container).toHaveTextContent('Free cancellation')
    expect(container).toHaveTextContent('up to 48 hours before the check-in day')
  })

  it('one hour is singular', () => {
    const { container } = renderNote(<PlanCancellationNote freeCancellation freeCancelHours={1} refundPercent={50} />)
    expect(container).toHaveTextContent('up to 1 hour before the check-in day')
  })

  it('a plan without a free window is not called free; a refund percent is told', () => {
    const { container } = renderNote(<PlanCancellationNote freeCancellation={false} freeCancelHours={null} refundPercent={50} />)
    expect(container).not.toHaveTextContent('Free cancellation')
    expect(container).toHaveTextContent('If you cancel, 50% of your payment is refunded.')
  })

  it('a non-refundable plan says so', () => {
    const { container } = renderNote(<PlanCancellationNote freeCancellation={false} freeCancelHours={null} refundPercent={0} />)
    expect(container).toHaveTextContent('Non-refundable')
  })

  it('an old API answer without the fields shows nothing', () => {
    const { container } = renderNote(<PlanCancellationNote freeCancellation={undefined} freeCancelHours={undefined} refundPercent={undefined} />)
    expect(container).toBeEmptyDOMElement()
  })
})
