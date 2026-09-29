/**
 * 3.7 bulk price edit: select a date range and (this screen's) one rate plan, set a
 * nightly price, apply. "Bulk price edit" is a secondary action next to the screen's
 * one primary button; the form it opens has its own single primary "Apply".
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { PartnerAvailabilityManagement } from './PartnerAvailabilityManagement'
import { partnerAdapter } from '../adapters/partnerAdapter'

vi.mock('../adapters/partnerAdapter', () => ({
  partnerAdapter: {
    getDateInventory: vi.fn(),
    bulkSetPrice: vi.fn(),
  },
}))

describe('PartnerAvailabilityManagement bulk price edit (3.7)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(partnerAdapter.getDateInventory).mockResolvedValue({ data: [], error: null })
  })

  it('is a secondary action next to the list view\'s one primary button', async () => {
    render(<PartnerAvailabilityManagement ratePlanId={11} ratePlanName="Standard Rate" />)

    const bulkButton = await screen.findByRole('button', { name: /bulk price edit/i })
    expect(bulkButton).toHaveClass('btn-secondary')
    expect(screen.getByRole('button', { name: 'Add new date inventory' })).toHaveClass('btn-primary')
  })

  it('applies a bulk price over a date range and returns to the list', async () => {
    vi.mocked(partnerAdapter.bulkSetPrice).mockResolvedValue({ data: [], error: null })
    render(<PartnerAvailabilityManagement ratePlanId={11} ratePlanName="Standard Rate" />)

    fireEvent.click(await screen.findByRole('button', { name: /bulk price edit/i }))
    expect(screen.getByRole('heading', { name: /bulk price edit/i })).toBeInTheDocument()
    // the list view's primary button is not rendered while the bulk form is open
    expect(screen.queryByRole('button', { name: 'Add new date inventory' })).not.toBeInTheDocument()

    fireEvent.change(screen.getByLabelText('From *'), { target: { value: '2026-10-01' } })
    fireEvent.change(screen.getByLabelText('To (exclusive) *'), { target: { value: '2026-10-05' } })
    fireEvent.change(screen.getByLabelText('Nightly price *'), { target: { value: '95' } })
    fireEvent.click(screen.getByRole('button', { name: 'Apply' }))

    await waitFor(() => expect(partnerAdapter.bulkSetPrice).toHaveBeenCalledWith({
      rate_plan: 11, date_from: '2026-10-01', date_to: '2026-10-05', price: 95,
    }))
    await waitFor(() => expect(screen.getByRole('button', { name: 'Add new date inventory' })).toBeInTheDocument())
    expect(partnerAdapter.getDateInventory).toHaveBeenCalledTimes(2) // initial load + reload after apply
  })

  it('shows the error and stays on the form when the bulk update fails', async () => {
    // A negative price is blocked by the input's own min="0" before it ever reaches
    // the handler, so this exercises a server-side rejection instead (e.g. ownership).
    vi.mocked(partnerAdapter.bulkSetPrice).mockResolvedValue({
      data: null, error: 'You can only manage inventory for your own properties.',
    })
    render(<PartnerAvailabilityManagement ratePlanId={11} ratePlanName="Standard Rate" />)

    fireEvent.click(await screen.findByRole('button', { name: /bulk price edit/i }))
    fireEvent.change(screen.getByLabelText('From *'), { target: { value: '2026-10-01' } })
    fireEvent.change(screen.getByLabelText('To (exclusive) *'), { target: { value: '2026-10-05' } })
    fireEvent.change(screen.getByLabelText('Nightly price *'), { target: { value: '95' } })
    fireEvent.click(screen.getByRole('button', { name: 'Apply' }))

    await waitFor(() => expect(partnerAdapter.bulkSetPrice).toHaveBeenCalled())
    expect(await screen.findByRole('alert')).toHaveTextContent(/own properties/)
    expect(screen.getByRole('heading', { name: /bulk price edit/i })).toBeInTheDocument()
  })
})
