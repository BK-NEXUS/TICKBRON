/**
 * R11: the owner sets the cancellation terms of a rate plan: a free window (hours before the check-in
 * day) and the percent refunded after it. The backend validates too; the form tells the owner first.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { PartnerRatesManagement } from './PartnerRatesManagement'
import { partnerAdapter } from '../adapters/partnerAdapter'

vi.mock('../adapters/partnerAdapter', () => ({
  partnerAdapter: { getRatePlans: vi.fn(), updateRatePlan: vi.fn(), createRatePlan: vi.fn(), deleteRatePlan: vi.fn() },
}))

const api = vi.mocked(partnerAdapter)

const plan = (patch = {}) => ({
  id: 11, room_type: 7, name: 'Standard Rate', slug: 'standard', rate_type: 'standard', description: '', base_price: 95,
  currency: 'USD', min_nights: 1, max_nights: 30, is_active: true, cancellation_policy: 'flexible',
  deposit_required: false, free_cancel_hours: null, cancel_refund_percent: null, ...patch,
}) as never

const HOURS = 'Free cancellation window (hours before the check-in day)'
const PERCENT = 'Refund after the free window (%)'

async function openEdit(ratePlan = plan()) {
  api.getRatePlans.mockResolvedValue({ data: [ratePlan], error: null })
  render(<PartnerRatesManagement roomTypeId={7} roomTypeName="Deluxe King" />)
  fireEvent.click(await screen.findByRole('button', { name: 'Edit Standard Rate' }))
  await screen.findByLabelText(HOURS)
}

const save = () => fireEvent.click(screen.getByRole('button', { name: 'Update Rate Plan' }))

describe('cancellation terms in the rate plan form', () => {
  beforeEach(() => {
    localStorage.clear()
    localStorage.setItem('tickbron.language', 'en')
    vi.resetAllMocks()
    api.updateRatePlan.mockResolvedValue({ data: plan(), error: null })
    api.createRatePlan.mockResolvedValue({ data: plan(), error: null })
  })

  it('shows the two fields empty for a plan that uses the platform defaults, with a hint each', async () => {
    await openEdit()
    expect(screen.getByLabelText(HOURS)).toHaveValue(null)
    expect(screen.getByLabelText(PERCENT)).toHaveValue(null)
    expect(screen.getByText(/Leave empty for no free cancellation/)).toBeInTheDocument()
    expect(screen.getByText(/Empty = the platform default/)).toBeInTheDocument()
  })

  it('shows what the plan has', async () => {
    await openEdit(plan({ free_cancel_hours: 48, cancel_refund_percent: 25 }))
    expect(screen.getByLabelText(HOURS)).toHaveValue(48)
    expect(screen.getByLabelText(PERCENT)).toHaveValue(25)
  })

  it('zero is a real value, not "empty"', async () => {
    await openEdit(plan({ free_cancel_hours: 0, cancel_refund_percent: 0 }))
    expect(screen.getByLabelText(HOURS)).toHaveValue(0)
    expect(screen.getByLabelText(PERCENT)).toHaveValue(0)
  })

  it('saves the numbers the owner typed', async () => {
    await openEdit()
    fireEvent.change(screen.getByLabelText(HOURS), { target: { value: '72' } })
    fireEvent.change(screen.getByLabelText(PERCENT), { target: { value: '30' } })
    save()
    await waitFor(() => expect(api.updateRatePlan).toHaveBeenCalledWith(11, expect.objectContaining({
      free_cancel_hours: 72, cancel_refund_percent: 30,
    })))
  })

  it('saves zero as zero', async () => {
    await openEdit()
    fireEvent.change(screen.getByLabelText(HOURS), { target: { value: '0' } })
    fireEvent.change(screen.getByLabelText(PERCENT), { target: { value: '0' } })
    save()
    await waitFor(() => expect(api.updateRatePlan).toHaveBeenCalledWith(11, expect.objectContaining({
      free_cancel_hours: 0, cancel_refund_percent: 0,
    })))
  })

  it('clearing a field sends null, so the plan goes back to no window / the platform percent', async () => {
    await openEdit(plan({ free_cancel_hours: 48, cancel_refund_percent: 25 }))
    fireEvent.change(screen.getByLabelText(HOURS), { target: { value: '' } })
    fireEvent.change(screen.getByLabelText(PERCENT), { target: { value: '' } })
    save()
    await waitFor(() => expect(api.updateRatePlan).toHaveBeenCalledWith(11, expect.objectContaining({
      free_cancel_hours: null, cancel_refund_percent: null,
    })))
  })

  it.each([
    [HOURS, '8761', 'Hours must be a whole number from 0 to 8760.'],
    [HOURS, '-1', 'Hours must be a whole number from 0 to 8760.'],
    [HOURS, '1.5', 'Hours must be a whole number from 0 to 8760.'],
    [PERCENT, '101', 'The percent must be a whole number from 0 to 100.'],
    [PERCENT, '-5', 'The percent must be a whole number from 0 to 100.'],
    [PERCENT, '12.5', 'The percent must be a whole number from 0 to 100.'],
  ])('refuses %s = %s before sending anything', async (label, value, message) => {
    await openEdit()
    fireEvent.change(screen.getByLabelText(label), { target: { value } })
    save()
    expect(await screen.findByRole('alert')).toHaveTextContent(message)
    expect(api.updateRatePlan).not.toHaveBeenCalled()
  })

  it('a new rate plan sends the terms only when the owner set them', async () => {
    api.getRatePlans.mockResolvedValue({ data: [], error: null })
    render(<PartnerRatesManagement roomTypeId={7} roomTypeName="Deluxe King" />)
    fireEvent.click(await screen.findByRole('button', { name: 'Add new rate plan' }))
    fireEvent.change(screen.getByLabelText(/Rate Plan Name/), { target: { value: 'Flex' } })
    fireEvent.change(screen.getByLabelText(/Slug/), { target: { value: 'flex' } })
    fireEvent.change(screen.getByLabelText(HOURS), { target: { value: '24' } })
    fireEvent.click(screen.getByRole('button', { name: 'Create Rate Plan' }))
    await waitFor(() => expect(api.createRatePlan).toHaveBeenCalledWith(expect.objectContaining({ free_cancel_hours: 24 })))
    // what goes over the wire: an unset term is simply absent
    expect(JSON.parse(JSON.stringify(api.createRatePlan.mock.calls[0][0]))).not.toHaveProperty('cancel_refund_percent')
  })
})
