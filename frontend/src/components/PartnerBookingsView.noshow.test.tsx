import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import { PartnerBookingsView } from './PartnerBookingsView'
import { I18nProvider } from '../i18n/I18nContext'
import { partnerAdapter, type PartnerBooking } from '../adapters/partnerAdapter'
import { noShowAdapter } from '../adapters/noShowAdapter'

vi.mock('../adapters/partnerAdapter', () => ({
  partnerAdapter: { getPartnerBookings: vi.fn() },
}))
vi.mock('../adapters/noShowAdapter', () => ({
  noShowAdapter: { reportNoShow: vi.fn() },
}))

function booking(id: number, extra: Partial<PartnerBooking> = {}): PartnerBooking {
  return {
    id, guest: 1, guest_name: `Guest ${id}`, property: 1, property_name: 'Silk Road Plaza', status: 'confirmed',
    payment_status: 'paid', check_in: '2026-10-05', check_out: '2026-10-07', number_of_nights: 2, guest_count: 2,
    total_price: 900000, currency: 'UZS', confirmation_code: `CODE${id}`, created_at: '2026-09-20T10:00:00Z',
    updated_at: '2026-09-20T10:00:00Z', can_report_no_show: false, report_deadline: null, ...extra,
  }
}

const getBookings = vi.mocked(partnerAdapter.getPartnerBookings)

function renderView() {
  render(
    <I18nProvider>
      <PartnerBookingsView />
    </I18nProvider>,
  )
}

describe('PartnerBookingsView no-show report', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    getBookings.mockResolvedValue({
      data: [booking(1, { can_report_no_show: true, report_deadline: '2026-10-14' }), booking(2)],
      error: null,
    })
  })

  it('offers the button only on bookings that can be reported, with the deadline', async () => {
    renderView()
    await screen.findByText('Guest 1')
    expect(screen.getAllByRole('button', { name: 'Guest did not arrive' })).toHaveLength(1)
    const card = screen.getByText('Guest 1').closest('.booking-card') as HTMLElement
    expect(within(card).getByRole('button', { name: 'Guest did not arrive' })).toBeInTheDocument()
    expect(within(card).getByText(/Report until/)).toHaveTextContent('14')
    const other = screen.getByText('Guest 2').closest('.booking-card') as HTMLElement
    expect(within(other).queryByRole('button', { name: 'Guest did not arrive' })).toBeNull()
  })

  it('opens the dialog for the chosen booking', async () => {
    renderView()
    fireEvent.click(await screen.findByRole('button', { name: 'Guest did not arrive' }))
    const dialog = await screen.findByRole('dialog')
    expect(dialog).toHaveTextContent('CODE1')
  })

  it('reloads the list after a report was sent and closes the dialog', async () => {
    vi.mocked(noShowAdapter.reportNoShow).mockResolvedValue({ data: { id: 5 } as never, error: null, code: null, fieldErrors: null })
    renderView()
    fireEvent.click(await screen.findByRole('button', { name: 'Guest did not arrive' }))
    const dialog = await screen.findByRole('dialog')
    fireEvent.change(within(dialog).getByLabelText('What happened? (required)'), {
      target: { value: 'The guest never arrived and did not answer.' },
    })
    getBookings.mockResolvedValue({ data: [booking(1), booking(2)], error: null })
    fireEvent.click(within(dialog).getByRole('button', { name: 'Send report' }))
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull())
    await waitFor(() => expect(getBookings).toHaveBeenCalledTimes(2))
    await waitFor(() => expect(screen.queryByRole('button', { name: 'Guest did not arrive' })).toBeNull())
    expect(await screen.findByRole('status', { name: 'Report sent' })).toBeInTheDocument()
  })

  it('has an only-reportable switch that asks the backend for reportable bookings', async () => {
    renderView()
    await screen.findByText('Guest 1')
    fireEvent.click(screen.getByLabelText('Only bookings I can still report'))
    await waitFor(() => expect(getBookings).toHaveBeenLastCalledWith(undefined, undefined, true))
    await screen.findByText('Guest 1')
  })

  it('keeps showing everything else the page showed before', async () => {
    renderView()
    expect(await screen.findByText('Guest 1')).toBeInTheDocument()
    expect(screen.getByLabelText('Filter by booking status')).toBeInTheDocument()
  })
})
