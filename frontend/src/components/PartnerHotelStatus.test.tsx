import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { PartnerHotelStatus } from './PartnerHotelStatus'
import { statusAdapter } from '../adapters/statusAdapter'
import { PARTNER_HOTEL } from '../test/statusFixtures'

vi.mock('../adapters/statusAdapter', () => ({
  statusAdapter: { getPartnerHotel: vi.fn(), getPartnerArrivals: vi.fn() },
}))

const getHotel = vi.mocked(statusAdapter.getPartnerHotel)
const getArrivals = vi.mocked(statusAdapter.getPartnerArrivals)

describe('PartnerHotelStatus', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    getHotel.mockResolvedValue({ data: PARTNER_HOTEL, error: null })
    getArrivals.mockResolvedValue({
      data: { count: 0, next: null, previous: null, results: [], day: 'today', date: '2026-10-07' }, error: null,
    })
  })

  it('shows a loading state first', () => {
    getHotel.mockReturnValue(new Promise(() => {}))
    render(<PartnerHotelStatus hotelId={1} onBack={vi.fn()} />)
    expect(screen.getByRole('status')).toHaveTextContent('Loading hotel...')
  })

  it('shows the own hotel overview: stats, series, reconciliation and arrivals of this hotel only', async () => {
    render(<PartnerHotelStatus hotelId={1} onBack={vi.fn()} />)

    expect(await screen.findByRole('heading', { name: 'Alpha Hotel' })).toBeInTheDocument()
    expect(getHotel).toHaveBeenCalledWith(1, { period: 'all' })
    expect(screen.getByText('Stayed')).toBeInTheDocument()
    expect(screen.getByRole('img', { name: 'Stayed bookings per month' })).toBeInTheDocument()
    expect(screen.getByRole('table', { name: 'Reconciliation' })).toBeInTheDocument()
    await waitFor(() => expect(getArrivals).toHaveBeenCalledWith({ day: 'today', property: 1, page: 1 }))
  })

  it('asks for another granularity, a preset and a custom range', async () => {
    render(<PartnerHotelStatus hotelId={1} onBack={vi.fn()} />)
    await screen.findByRole('heading', { name: 'Alpha Hotel' })

    fireEvent.change(screen.getByLabelText('Group by'), { target: { value: 'day' } })
    await waitFor(() => expect(getHotel).toHaveBeenLastCalledWith(1, { period: 'all', granularity: 'day' }))

    fireEvent.change(screen.getByLabelText('Period'), { target: { value: 'last_7_days' } })
    await waitFor(() => expect(getHotel).toHaveBeenLastCalledWith(1, { period: 'last_7_days', granularity: 'day' }))

    fireEvent.change(screen.getByLabelText('Period'), { target: { value: 'custom' } })
    fireEvent.change(screen.getByLabelText('From'), { target: { value: '2026-01-01' } })
    fireEvent.change(screen.getByLabelText('To'), { target: { value: '2026-03-01' } })
    fireEvent.click(screen.getByRole('button', { name: 'Apply' }))
    await waitFor(() => expect(getHotel).toHaveBeenLastCalledWith(
      1, { period: 'custom', from: '2026-01-01', to: '2026-03-01', granularity: 'day' }))
  })

  it("another owner's hotel shows a clear not-found page with a way back", async () => {
    getHotel.mockResolvedValue({ data: null, error: 'Not found', status: 404 })
    const onBack = vi.fn()
    render(<PartnerHotelStatus hotelId={999} onBack={onBack} />)

    expect(await screen.findByRole('heading', { name: 'Hotel not found' })).toBeInTheDocument()
    expect(screen.getByText('This hotel does not exist or is not one of yours.')).toBeInTheDocument()
    expect(screen.queryByRole('table', { name: 'Reconciliation' })).not.toBeInTheDocument()
    expect(getArrivals).not.toHaveBeenCalled()

    fireEvent.click(screen.getByRole('button', { name: 'Back to Status' }))
    expect(onBack).toHaveBeenCalled()
  })

  it('shows other errors as an alert', async () => {
    getHotel.mockResolvedValue({ data: null, error: 'Hotel owner role required', status: 403 })
    render(<PartnerHotelStatus hotelId={1} onBack={vi.fn()} />)

    expect(await screen.findByRole('alert')).toHaveTextContent('Hotel owner role required')
    expect(screen.queryByRole('heading', { name: 'Hotel not found' })).not.toBeInTheDocument()
  })

  it('keeps the period controls after a backend validation error', async () => {
    getHotel.mockResolvedValueOnce({ data: PARTNER_HOTEL, error: null })
    getHotel.mockResolvedValueOnce({ data: null, error: 'The range can be at most 20 years.', status: 400 })
    render(<PartnerHotelStatus hotelId={1} onBack={vi.fn()} />)
    await screen.findByRole('heading', { name: 'Alpha Hotel' })

    fireEvent.change(screen.getByLabelText('Period'), { target: { value: 'last_10_years' } })

    expect(await screen.findByRole('alert')).toHaveTextContent('at most 20 years')
    expect(screen.getByLabelText('Period')).toHaveValue('last_10_years')
  })

  it('never renders API text as HTML', async () => {
    getHotel.mockResolvedValue({
      data: { ...PARTNER_HOTEL, hotel: { ...PARTNER_HOTEL.hotel, name: '<img src=x onerror=alert(1)>' } }, error: null,
    })
    const { container } = render(<PartnerHotelStatus hotelId={1} onBack={vi.fn()} />)

    expect(await screen.findByRole('heading', { name: '<img src=x onerror=alert(1)>' })).toBeInTheDocument()
    expect(container.querySelector('img')).toBeNull()
  })
})
