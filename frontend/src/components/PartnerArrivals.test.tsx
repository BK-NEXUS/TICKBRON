import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import { PartnerArrivals } from './PartnerArrivals'
import { statusAdapter } from '../adapters/statusAdapter'

vi.mock('../adapters/statusAdapter', () => ({
  statusAdapter: { getPartnerArrivals: vi.fn() },
}))

const getArrivals = vi.mocked(statusAdapter.getPartnerArrivals)

const ARRIVAL = {
  id: 1, reference: 'TB-1', property: { id: 7, name: 'Hotel A' }, guest_name: 'Aziz K.', room_types: ['Double', 'Twin'],
  rooms: 2, nights: 3, guests: 4, check_in: '2026-10-07', check_out: '2026-10-10', special_requests: 'Late arrival', phone_last4: '1234',
}

const pageOf = (results: unknown[], extra: Record<string, unknown> = {}) => ({
  data: { count: results.length, next: null, previous: null, day: 'today', date: '2026-10-07', results, ...extra },
  error: null,
}) as never

describe('PartnerArrivals', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    getArrivals.mockResolvedValue(pageOf([ARRIVAL]))
  })

  it('shows today by default with the guest, rooms and only the last 4 phone digits', async () => {
    render(<PartnerArrivals />)

    const row = (await screen.findByText('TB-1')).closest('tr') as HTMLElement
    expect(getArrivals).toHaveBeenCalledWith({ day: 'today', page: 1 })
    expect(within(row).getByText('Aziz K.')).toBeInTheDocument()
    expect(within(row).getByText('Double, Twin')).toBeInTheDocument()
    expect(within(row).getByText('Hotel A')).toBeInTheDocument()
    expect(within(row).getByText('•••• 1234')).toBeInTheDocument()
    expect(within(row).getByText('Late arrival')).toBeInTheDocument()
    expect(document.querySelector('.status-controls .status-card-caption')).toHaveTextContent('Oct 7, 2026')
  })

  it('switches to tomorrow and starts from the first page', async () => {
    render(<PartnerArrivals />)
    await screen.findByText('TB-1')

    fireEvent.click(screen.getByRole('button', { name: 'Tomorrow' }))

    await waitFor(() => expect(getArrivals).toHaveBeenLastCalledWith({ day: 'tomorrow', page: 1 }))
    expect(screen.getByRole('button', { name: 'Tomorrow' })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: 'Today' })).toHaveAttribute('aria-pressed', 'false')
  })

  it('limits to one hotel and hides the hotel column', async () => {
    render(<PartnerArrivals propertyId={7} />)
    await screen.findByText('TB-1')

    expect(getArrivals).toHaveBeenCalledWith({ day: 'today', property: 7, page: 1 })
    expect(screen.queryByRole('columnheader', { name: 'Hotel' })).not.toBeInTheDocument()
  })

  it('paginates 50 per page', async () => {
    getArrivals.mockResolvedValue(pageOf([ARRIVAL], { count: 120, next: 'http://x/?page=2' }))
    render(<PartnerArrivals />)
    await screen.findByText('Page 1 of 3')

    fireEvent.click(screen.getByRole('button', { name: 'Next page' }))

    await waitFor(() => expect(getArrivals).toHaveBeenLastCalledWith({ day: 'today', page: 2 }))
  })

  it('shows loading, empty and error states', async () => {
    getArrivals.mockReturnValueOnce(new Promise(() => {}))
    const loading = render(<PartnerArrivals />)
    expect(screen.getByRole('status')).toHaveTextContent('Loading arrivals...')
    loading.unmount()

    getArrivals.mockResolvedValue(pageOf([]))
    const empty = render(<PartnerArrivals />)
    expect(await screen.findByText('No arrivals today.')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Tomorrow' }))
    expect(await screen.findByText('No arrivals tomorrow.')).toBeInTheDocument()
    empty.unmount()

    getArrivals.mockResolvedValue({ data: null, error: 'Hotel owner role required' })
    render(<PartnerArrivals />)
    expect(await screen.findByRole('alert')).toHaveTextContent('Hotel owner role required')
  })

  it('never renders guest text as HTML', async () => {
    getArrivals.mockResolvedValue(pageOf([{ ...ARRIVAL, special_requests: '<img src=x onerror=alert(1)>' }]))
    const { container } = render(<PartnerArrivals />)

    expect(await screen.findByText('<img src=x onerror=alert(1)>')).toBeInTheDocument()
    expect(container.querySelector('img')).toBeNull()
  })
})
