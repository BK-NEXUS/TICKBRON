/**
 * Cash at the hotel: the owner sees the arrival time each guest gave and marks "Guest arrived";
 * a confirmed booking with no mark is cancelled by the system 2 hours after that time.
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import { PartnerArrivals } from './PartnerArrivals'
import { statusAdapter } from '../adapters/statusAdapter'
import { partnerAdapter } from '../adapters/partnerAdapter'

vi.mock('../adapters/statusAdapter', () => ({ statusAdapter: { getPartnerArrivals: vi.fn() } }))
vi.mock('../adapters/partnerAdapter', () => ({ partnerAdapter: { markGuestArrived: vi.fn() } }))

const getArrivals = vi.mocked(statusAdapter.getPartnerArrivals)
const markArrived = vi.mocked(partnerAdapter.markGuestArrived)

const arrival = (over: object) => ({
  id: 1, reference: 'TB-1', property: { id: 7, name: 'Hotel A' }, guest_name: 'Aziz K.', room_types: ['Double'],
  rooms: 1, nights: 2, guests: 2, check_in: '2026-10-07', check_out: '2026-10-09', special_requests: '',
  phone: '+998 90 333-12-34', expected_arrival_time: '10:30', arrived_at: null, ...over,
})

const page = (results: unknown[]) => ({
  data: { count: results.length, next: null, previous: null, day: 'today', date: '2026-10-07', results }, error: null,
}) as never

describe('PartnerArrivals: guest arrived', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    getArrivals.mockResolvedValue(page([arrival({})]))
    markArrived.mockResolvedValue({ data: { id: 1, arrived_at: '2026-10-07T05:40:00Z' }, error: null } as never)
  })

  it('shows the arrival time the guest gave', async () => {
    render(<PartnerArrivals />)
    const row = (await screen.findByText('TB-1')).closest('tr') as HTMLElement
    expect(within(row).getByText('10:30')).toBeInTheDocument()
  })

  it('an old booking without an arrival time shows a dash', async () => {
    getArrivals.mockResolvedValue(page([arrival({ expected_arrival_time: null })]))
    render(<PartnerArrivals />)
    const row = (await screen.findByText('TB-1')).closest('tr') as HTMLElement
    expect(within(row).getAllByText('—').length).toBeGreaterThan(0)
  })

  it('marks the guest as arrived and then shows it instead of the button', async () => {
    render(<PartnerArrivals />)
    fireEvent.click(await screen.findByRole('button', { name: 'Guest arrived: TB-1' }))
    await waitFor(() => expect(markArrived).toHaveBeenCalledWith(1))
    expect(await screen.findByText('Arrived')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Guest arrived: TB-1' })).not.toBeInTheDocument()
  })

  it('an already arrived guest has no button', async () => {
    getArrivals.mockResolvedValue(page([arrival({ arrived_at: '2026-10-07T05:40:00Z' })]))
    render(<PartnerArrivals />)
    expect(await screen.findByText('Arrived')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Guest arrived/ })).not.toBeInTheDocument()
  })

  it('tomorrow\'s guests cannot be marked yet', async () => {
    render(<PartnerArrivals />)
    await screen.findByText('TB-1')
    getArrivals.mockResolvedValue(page([arrival({ id: 2, reference: 'TB-2', check_in: '2026-10-08' })]))
    fireEvent.click(screen.getByRole('button', { name: 'Tomorrow' }))
    await screen.findByText('TB-2')
    expect(screen.queryByRole('button', { name: /Guest arrived/ })).not.toBeInTheDocument()
  })

  it('shows the reason when marking fails and keeps the button', async () => {
    markArrived.mockResolvedValue({ data: null, error: 'Only a confirmed booking can be marked as arrived.' } as never)
    render(<PartnerArrivals />)
    fireEvent.click(await screen.findByRole('button', { name: 'Guest arrived: TB-1' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Only a confirmed booking can be marked as arrived.')
    expect(screen.getByRole('button', { name: 'Guest arrived: TB-1' })).toBeEnabled()
  })

  it('explains the rule once', async () => {
    render(<PartnerArrivals />)
    await screen.findByText('TB-1')
    expect(screen.getByText(/not marked as arrived 2 hours after the arrival time is cancelled/i)).toBeInTheDocument()
  })
})
