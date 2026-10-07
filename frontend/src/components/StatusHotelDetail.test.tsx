import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import { StatusHotelDetail } from './StatusHotelDetail'
import { statusAdapter } from '../adapters/statusAdapter'
import { HOTEL_DETAIL } from '../test/statusFixtures'

vi.mock('../adapters/statusAdapter', () => ({
  statusAdapter: { getHotelDetail: vi.fn() },
}))

const getDetail = vi.mocked(statusAdapter.getHotelDetail)

function renderDetail(props: Partial<React.ComponentProps<typeof StatusHotelDetail>> = {}) {
  const onPeriodChange = vi.fn()
  const onRangeChange = vi.fn()
  render(
    <StatusHotelDetail
      hotelId={11} period="all" onPeriodChange={onPeriodChange} onRangeChange={onRangeChange} {...props}
    />,
  )
  return { onPeriodChange, onRangeChange }
}

describe('StatusHotelDetail (R12a)', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    getDetail.mockResolvedValue({ data: HOTEL_DETAIL, error: null })
  })

  it('shows a loading state first', () => {
    getDetail.mockReturnValue(new Promise(() => {}))
    renderDetail()
    expect(screen.getByRole('status')).toHaveTextContent('Loading hotel...')
  })

  it('leads with stayed, keeps counted and upcoming apart, and lists status counts', async () => {
    renderDetail()
    await screen.findByRole('heading', { name: 'Alpha Hotel' })

    expect(screen.getByText('Stayed').closest('.status-card')).toHaveClass('status-card--headline')
    expect(within(screen.getByText('Counted').closest('.status-card') as HTMLElement).getByText('1,500')).toBeInTheDocument()
    expect(within(screen.getByText('Upcoming').closest('.status-card') as HTMLElement).getByText('42')).toBeInTheDocument()
    const statuses = screen.getByRole('list', { name: 'Bookings by status' })
    expect(within(statuses).getByText('Cancelled').nextSibling).toHaveTextContent('30')
  })

  it('shows the reconciliation block and the may-still-change note', async () => {
    renderDetail()
    await screen.findByRole('heading', { name: 'Alpha Hotel' })

    const table = screen.getByRole('table', { name: 'Reconciliation' })
    expect(within(table).getByText('This week')).toBeInTheDocument()
    expect(screen.getAllByRole('note').length).toBeGreaterThan(0)
  })

  it('charts the series by the chosen granularity and asks the backend for it', async () => {
    renderDetail()
    await screen.findByRole('img', { name: 'Stayed bookings per month' })

    fireEvent.change(screen.getByLabelText('Group by'), { target: { value: 'week' } })

    await waitFor(() => expect(getDetail).toHaveBeenLastCalledWith(11, { period: 'all', granularity: 'week' }))
  })

  it('a custom range reaches the backend as period custom with from and to', async () => {
    const { onRangeChange } = renderDetail({ range: null })
    await screen.findByRole('heading', { name: 'Alpha Hotel' })

    fireEvent.change(screen.getByLabelText('Period'), { target: { value: 'custom' } })
    fireEvent.change(screen.getByLabelText('From'), { target: { value: '2026-01-01' } })
    fireEvent.change(screen.getByLabelText('To'), { target: { value: '2026-03-01' } })
    fireEvent.click(screen.getByRole('button', { name: 'Apply' }))

    expect(onRangeChange).toHaveBeenCalledWith({ from: '2026-01-01', to: '2026-03-01' })
  })

  it('requests the applied custom range', async () => {
    renderDetail({ period: 'custom', range: { from: '2026-01-01', to: '2026-03-01' } })
    await screen.findByRole('heading', { name: 'Alpha Hotel' })

    expect(getDetail).toHaveBeenCalledWith(11, { period: 'custom', from: '2026-01-01', to: '2026-03-01' })
  })

  it('shows the backend message inline and keeps the period controls usable', async () => {
    getDetail.mockResolvedValueOnce({ data: HOTEL_DETAIL, error: null })
    getDetail.mockResolvedValueOnce({ data: null, error: 'The range can be at most 20 years.' })
    const { rerender } = render(
      <StatusHotelDetail hotelId={11} period="all" onPeriodChange={vi.fn()} onRangeChange={vi.fn()} />)
    await screen.findByRole('heading', { name: 'Alpha Hotel' })

    rerender(<StatusHotelDetail hotelId={11} period="last_10_years" onPeriodChange={vi.fn()} onRangeChange={vi.fn()} />)

    expect(await screen.findByRole('alert')).toHaveTextContent('The range can be at most 20 years.')
    expect(screen.getByLabelText('Period')).toBeEnabled()
    expect(screen.queryByRole('table', { name: 'Reconciliation' })).not.toBeInTheDocument()
  })

  it('shows an error when the hotel cannot be loaded', async () => {
    getDetail.mockResolvedValue({ data: null, error: 'Not found' })
    renderDetail()
    expect(await screen.findByRole('alert')).toHaveTextContent('Not found')
  })

  it('never renders API text as HTML', async () => {
    const hostile = { ...HOTEL_DETAIL, hotel: { ...HOTEL_DETAIL.hotel, name: '<img src=x onerror=alert(1)>' } }
    getDetail.mockResolvedValue({ data: hostile, error: null })
    const { container } = render(
      <StatusHotelDetail hotelId={11} period="all" onPeriodChange={vi.fn()} onRangeChange={vi.fn()} />)

    expect(await screen.findByRole('heading', { name: '<img src=x onerror=alert(1)>' })).toBeInTheDocument()
    expect(container.querySelector('img')).toBeNull()
  })
})
