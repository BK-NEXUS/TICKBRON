import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { PartnerBookingsView } from './PartnerBookingsView'
import { I18nProvider } from '../i18n/I18nContext'
import { partnerAdapter } from '../adapters/partnerAdapter'
import { statusAdapter } from '../adapters/statusAdapter'
import { saveBlob } from '../utils/saveBlob'

vi.mock('../adapters/partnerAdapter', () => ({
  partnerAdapter: { getPartnerBookings: vi.fn() },
}))
vi.mock('../adapters/statusAdapter', () => ({
  statusAdapter: { exportPartnerBookings: vi.fn() },
}))
vi.mock('../utils/saveBlob', () => ({ saveBlob: vi.fn() }))

const getBookings = vi.mocked(partnerAdapter.getPartnerBookings)
const exportBookings = vi.mocked(statusAdapter.exportPartnerBookings)

function renderView() {
  render(
    <I18nProvider>
      <PartnerBookingsView />
    </I18nProvider>,
  )
}

describe('PartnerBookingsView export', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    getBookings.mockResolvedValue({ data: [], error: null })
  })

  it('shows CSV and Excel buttons even when the list is empty', async () => {
    renderView()
    expect(await screen.findByRole('button', { name: 'Export CSV' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Export Excel' })).toBeInTheDocument()
  })

  it('downloads the file with the filters that are on screen', async () => {
    const file = { blob: new Blob(['x']), filename: 'partner_bookings.csv' }
    exportBookings.mockResolvedValue({ data: file, error: null })
    renderView()
    fireEvent.change(await screen.findByLabelText('Filter by booking status'), { target: { value: 'confirmed' } })
    fireEvent.click(screen.getByLabelText('Only bookings I can still report'))
    await waitFor(() => expect(getBookings).toHaveBeenLastCalledWith('confirmed', undefined, true))

    fireEvent.click(screen.getByRole('button', { name: 'Export CSV' }))

    await waitFor(() => expect(saveBlob).toHaveBeenCalledWith(file.blob, 'partner_bookings.csv'))
    expect(exportBookings).toHaveBeenCalledWith(
      { status: 'confirmed', paymentStatus: undefined, reportableOnly: true }, 'csv')
  })

  it('asks for Excel with the Excel button', async () => {
    exportBookings.mockResolvedValue({ data: { blob: new Blob(['x']), filename: 'partner_bookings.xlsx' }, error: null })
    renderView()
    fireEvent.click(await screen.findByRole('button', { name: 'Export Excel' }))
    await waitFor(() => expect(exportBookings).toHaveBeenCalledWith(
      { status: undefined, paymentStatus: undefined, reportableOnly: false }, 'xlsx'))
  })

  it('shows why the export failed and saves nothing', async () => {
    exportBookings.mockResolvedValue({ data: null, error: 'Too many rows' })
    renderView()
    fireEvent.click(await screen.findByRole('button', { name: 'Export CSV' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Too many rows')
    expect(saveBlob).not.toHaveBeenCalled()
  })
})
