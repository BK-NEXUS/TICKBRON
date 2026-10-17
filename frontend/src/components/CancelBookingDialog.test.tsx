import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { CancelBookingDialog } from './CancelBookingDialog'
import { I18nProvider } from '../i18n/I18nContext'
import { bookingAdapter, type CancelPreview } from '../adapters/bookingAdapter'

vi.mock('../adapters/bookingAdapter', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../adapters/bookingAdapter')>()),
  bookingAdapter: { getCancelPreview: vi.fn(), cancelBooking: vi.fn() },
}))

const api = vi.mocked(bookingAdapter)

const preview = (patch: Partial<CancelPreview> = {}): { data: CancelPreview; error: null } => ({
  data: { refund_amount: '1177295.00', refund_currency: 'UZS', refund_percent: 50, free_until: null, ...patch }, error: null,
})

function renderDialog() {
  localStorage.setItem('tickbron.language', 'en')
  const onClose = vi.fn()
  const onCancelled = vi.fn()
  render(<I18nProvider><CancelBookingDialog bookingId={7} onClose={onClose} onCancelled={onCancelled} /></I18nProvider>)
  return { onClose, onCancelled }
}

const confirmButton = () => screen.getByRole('button', { name: /Yes, cancel booking|Cancelling/ })

describe('CancelBookingDialog', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.resetAllMocks()
    api.getCancelPreview.mockResolvedValue(preview())
    api.cancelBooking.mockResolvedValue({ data: { id: 7, status: 'cancelled', refund: { amount: '1177295.00', currency: 'UZS', percent: 50 } } as never, error: null })
  })

  it('asks the backend what the guest would get back before anything is cancelled', async () => {
    renderDialog()
    expect(screen.getByText('Checking what you would get back...')).toBeInTheDocument()
    expect(confirmButton()).toBeDisabled()
    expect(await screen.findByText(/If you cancel now, 1 177 295 UZS \(50%\) is refunded/)).toBeInTheDocument()
    expect(api.getCancelPreview).toHaveBeenCalledWith(7)
    expect(api.cancelBooking).not.toHaveBeenCalled()
    expect(confirmButton()).toBeEnabled()
  })

  it('a non-refundable booking says there is no refund', async () => {
    api.getCancelPreview.mockResolvedValue(preview({ refund_amount: '0.00', refund_percent: 0 }))
    renderDialog()
    expect(await screen.findByText('This booking is non-refundable: you will not get a refund.')).toBeInTheDocument()
  })

  it('a booking nothing was paid for says nothing is refunded', async () => {
    api.getCancelPreview.mockResolvedValue(preview({ refund_amount: '0.00', refund_percent: 50 }))
    renderDialog()
    expect(await screen.findByText('Nothing has been paid for this booking, so nothing is refunded.')).toBeInTheDocument()
  })

  it('an older booking without terms says there is no automatic refund', async () => {
    api.getCancelPreview.mockResolvedValue(preview({ refund_amount: '0.00', refund_percent: null }))
    renderDialog()
    expect(await screen.findByText(/no automatic refund/)).toBeInTheDocument()
  })

  it('confirming cancels the booking and hands the result over', async () => {
    const { onCancelled } = renderDialog()
    await screen.findByText(/is refunded/)
    fireEvent.click(confirmButton())
    await waitFor(() => expect(api.cancelBooking).toHaveBeenCalledWith(7))
    await waitFor(() => expect(onCancelled).toHaveBeenCalledWith(
      expect.objectContaining({ status: 'cancelled', refund: { amount: '1177295.00', currency: 'UZS', percent: 50 } })))
  })

  it('shows a cancel that fails, keeps the dialog open and lets the guest try again', async () => {
    api.cancelBooking.mockResolvedValueOnce({ data: null, error: 'A stay that has started cannot be cancelled online.' })
    const { onCancelled } = renderDialog()
    await screen.findByText(/is refunded/)
    fireEvent.click(confirmButton())
    expect(await screen.findByRole('alert')).toHaveTextContent('A stay that has started cannot be cancelled online.')
    expect(onCancelled).not.toHaveBeenCalled()
    expect(confirmButton()).toBeEnabled()
  })

  it('a preview that cannot be loaded shows the reason and offers no cancel', async () => {
    api.getCancelPreview.mockResolvedValueOnce({ data: null, error: 'A stay that has started cannot be cancelled online.' })
    renderDialog()
    expect(await screen.findByRole('alert')).toHaveTextContent('A stay that has started cannot be cancelled online.')
    expect(confirmButton()).toBeDisabled()
    fireEvent.click(screen.getByRole('button', { name: 'Try Again' }))
    await screen.findByText(/is refunded/)
    expect(confirmButton()).toBeEnabled()
  })

  it('Keep booking closes it without cancelling', async () => {
    const { onClose } = renderDialog()
    await screen.findByText(/is refunded/)
    fireEvent.click(screen.getByRole('button', { name: 'Keep booking' }))
    expect(onClose).toHaveBeenCalled()
    expect(api.cancelBooking).not.toHaveBeenCalled()
  })
})
