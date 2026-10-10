import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import { PartnerNoShowReports } from './PartnerNoShowReports'
import { I18nProvider } from '../i18n/I18nContext'
import { noShowAdapter, type OwnerNoShowReport } from '../adapters/noShowAdapter'

vi.mock('../adapters/noShowAdapter', () => ({
  noShowAdapter: { listMyReports: vi.fn(), withdrawReport: vi.fn() },
}))

const adapter = vi.mocked(noShowAdapter)
const properties = [{ id: 3, name: 'Silk Road Plaza' }, { id: 4, name: 'Registan Inn' }]

function report(id: number, extra: Partial<OwnerNoShowReport> = {}): OwnerNoShowReport {
  return {
    id, booking_id: id * 10, booking_reference: `REF${id}`, property_id: 3, property_name: 'Silk Road Plaza',
    check_in: '2026-10-05', check_out: '2026-10-07', comment: `Owner comment ${id}`, status: 'pending',
    decision_comment: '', decided_at: null, created_at: '2026-10-08T10:00:00Z', ...extra,
  }
}

function page(results: OwnerNoShowReport[], count = results.length) {
  return { data: { count, next: null, previous: null, results }, error: null, code: null, fieldErrors: null }
}

function renderScreen() {
  render(
    <I18nProvider>
      <PartnerNoShowReports properties={properties} />
    </I18nProvider>,
  )
}

describe('PartnerNoShowReports', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    adapter.listMyReports.mockResolvedValue(page([report(1)]))
  })

  it('lists my reports with the booking, the status and my comment', async () => {
    adapter.listMyReports.mockResolvedValue(page([
      report(1),
      report(2, { status: 'approved', decision_comment: 'Confirmed with the guest', decided_at: '2026-10-09T08:00:00Z' }),
      report(3, { status: 'rejected', decision_comment: 'Guest checked in late' }),
      report(4, { status: 'withdrawn' }),
    ]))
    renderScreen()
    const items = await screen.findAllByRole('listitem')
    expect(items).toHaveLength(4)
    expect(within(items[0]).getByText('REF1')).toBeInTheDocument()
    expect(within(items[0]).getByText('Waiting for a decision')).toBeInTheDocument()
    expect(within(items[0]).getByText('Owner comment 1')).toBeInTheDocument()
    expect(within(items[1]).getByText('Approved')).toBeInTheDocument()
    expect(within(items[1]).getByText('Confirmed with the guest')).toBeInTheDocument()
    expect(within(items[2]).getByText('Rejected')).toBeInTheDocument()
    expect(within(items[3]).getByText('Withdrawn')).toBeInTheDocument()
  })

  it('shows loading, then an empty message', async () => {
    adapter.listMyReports.mockResolvedValue(page([]))
    renderScreen()
    expect(screen.getByText('Loading reports...')).toBeInTheDocument()
    expect(await screen.findByText('You have not sent any reports yet.')).toBeInTheDocument()
  })

  it('shows an error with a retry', async () => {
    adapter.listMyReports.mockResolvedValueOnce({ data: null, error: 'boom', code: null, fieldErrors: null })
    renderScreen()
    expect(await screen.findByRole('alert')).toHaveTextContent('Could not load your reports.')
    adapter.listMyReports.mockResolvedValue(page([report(1)]))
    fireEvent.click(screen.getByRole('button', { name: 'Try Again' }))
    expect(await screen.findByText('REF1')).toBeInTheDocument()
  })

  it('filters by status and by hotel', async () => {
    renderScreen()
    await screen.findByText('REF1')
    fireEvent.change(screen.getByLabelText('Status'), { target: { value: 'approved' } })
    await waitFor(() => expect(adapter.listMyReports).toHaveBeenLastCalledWith(expect.objectContaining({ status: 'approved', page: 1 })))
    fireEvent.change(screen.getByLabelText('Hotel'), { target: { value: '4' } })
    await waitFor(() => expect(adapter.listMyReports).toHaveBeenLastCalledWith(expect.objectContaining({ property: 4, status: 'approved' })))
    await screen.findByText('REF1')
  })

  it('goes to the next page', async () => {
    adapter.listMyReports.mockResolvedValue({
      data: { count: 45, next: 'x', previous: null, results: [report(1)] }, error: null, code: null, fieldErrors: null,
    })
    renderScreen()
    await screen.findByText('REF1')
    fireEvent.click(screen.getByRole('button', { name: 'Next page' }))
    await waitFor(() => expect(adapter.listMyReports).toHaveBeenLastCalledWith(expect.objectContaining({ page: 2 })))
    await screen.findByText('REF1')
  })

  it('withdraws a waiting report and reloads', async () => {
    adapter.withdrawReport.mockResolvedValue({ data: report(1, { status: 'withdrawn' }), error: null, code: null, fieldErrors: null })
    renderScreen()
    fireEvent.click(await screen.findByRole('button', { name: 'Withdraw report' }))
    await waitFor(() => expect(adapter.withdrawReport).toHaveBeenCalledWith(1))
    await waitFor(() => expect(adapter.listMyReports).toHaveBeenCalledTimes(2))
    await screen.findByText('REF1')
  })

  it('offers withdraw only for waiting reports', async () => {
    adapter.listMyReports.mockResolvedValue(page([report(1, { status: 'approved' }), report(2, { status: 'rejected' })]))
    renderScreen()
    await screen.findByText('REF1')
    expect(screen.queryByRole('button', { name: 'Withdraw report' })).toBeNull()
  })

  it('shows a translated message when withdrawing fails', async () => {
    adapter.withdrawReport.mockResolvedValue({ data: null, error: 'x', code: 'not_pending', fieldErrors: null })
    renderScreen()
    fireEvent.click(await screen.findByRole('button', { name: 'Withdraw report' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('This report has already been decided or withdrawn.')
  })
})
