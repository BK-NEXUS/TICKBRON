import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { CancelBookingDialog } from './CancelBookingDialog'
import { I18nProvider } from '../i18n/I18nContext'
import { bookingAdapter } from '../adapters/bookingAdapter'

vi.mock('../adapters/bookingAdapter', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../adapters/bookingAdapter')>()),
  bookingAdapter: { cancelBooking: vi.fn() },
}))

const api = vi.mocked(bookingAdapter)

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
    api.cancelBooking.mockResolvedValue({ data: { id: 7, status: 'cancelled' } as never, error: null })
  })

  it('says cancelling is free and cancels nothing until the guest confirms', () => {
    renderDialog()
    expect(screen.getByText(/Cancelling is free/)).toBeInTheDocument()
    expect(confirmButton()).toBeEnabled()
    expect(api.cancelBooking).not.toHaveBeenCalled()
  })

  it('confirming cancels the booking and hands the result over', async () => {
    const { onCancelled } = renderDialog()
    fireEvent.click(confirmButton())
    await waitFor(() => expect(onCancelled).toHaveBeenCalledWith({ id: 7, status: 'cancelled' }))
    expect(api.cancelBooking).toHaveBeenCalledWith(7)
  })

  it('shows a cancel that fails, keeps the dialog open and lets the guest try again', async () => {
    api.cancelBooking.mockResolvedValueOnce({ data: null, error: 'A stay that has started cannot be cancelled online.' })
    const { onCancelled } = renderDialog()
    fireEvent.click(confirmButton())
    expect(await screen.findByRole('alert')).toHaveTextContent('A stay that has started cannot be cancelled online.')
    expect(onCancelled).not.toHaveBeenCalled()
    fireEvent.click(confirmButton())
    await waitFor(() => expect(onCancelled).toHaveBeenCalled())
    expect(api.cancelBooking).toHaveBeenCalledTimes(2)
  })

  it('Keep booking closes it without cancelling', () => {
    const { onClose } = renderDialog()
    fireEvent.click(screen.getByRole('button', { name: 'Keep booking' }))
    expect(onClose).toHaveBeenCalled()
    expect(api.cancelBooking).not.toHaveBeenCalled()
  })
})
