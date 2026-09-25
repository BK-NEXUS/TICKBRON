/**
 * E2E BUG 3: room type cards lead to their rate plans, rate plan cards to their availability.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { PartnerRoomsManagement } from './PartnerRoomsManagement'
import { PartnerRatesManagement } from './PartnerRatesManagement'
import { partnerAdapter } from '../adapters/partnerAdapter'

vi.mock('../adapters/partnerAdapter', () => ({
  partnerAdapter: { getRoomTypes: vi.fn(), getRatePlans: vi.fn() },
}))

describe('partner room type and rate plan cards', () => {
  beforeEach(() => {
    vi.mocked(partnerAdapter.getRoomTypes).mockResolvedValue({
      data: [{ id: 7, property: 3, name: 'Deluxe King', slug: 'deluxe-king', base_occupancy: 2, max_occupancy: 3,
        base_price: 95, currency: 'USD', total_rooms: 4, bed_configuration: '1 King Bed' } as never],
      error: null,
    })
    vi.mocked(partnerAdapter.getRatePlans).mockResolvedValue({
      data: [{ id: 11, room_type: 7, name: 'Standard Rate', slug: 'standard', rate_type: 'standard', base_price: 95,
        currency: 'USD', min_nights: 1, max_nights: 30, is_active: true } as never],
      error: null,
    })
  })

  it('opens the rate plans of a room type', async () => {
    const onManageRates = vi.fn()
    render(<PartnerRoomsManagement propertyId={3} propertyName="Tashkent" onManageRates={onManageRates} />)

    fireEvent.click(await screen.findByRole('button', { name: 'Manage rates and availability for Deluxe King' }))

    expect(onManageRates).toHaveBeenCalledWith({ id: 7, name: 'Deluxe King' })
  })

  it('opens the availability of a rate plan', async () => {
    const onManageAvailability = vi.fn()
    render(<PartnerRatesManagement roomTypeId={7} roomTypeName="Deluxe King" onManageAvailability={onManageAvailability} />)

    fireEvent.click(await screen.findByRole('button', { name: 'Manage availability for Standard Rate' }))

    expect(onManageAvailability).toHaveBeenCalledWith({ id: 11, name: 'Standard Rate' })
  })
})
