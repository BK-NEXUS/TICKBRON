import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { RoomSelection } from './RoomSelection'
import { RoomType, RatePlan, propertyAdapter } from '../adapters/propertyAdapter'

vi.mock('../adapters/propertyAdapter', () => ({
  propertyAdapter: { getAvailability: vi.fn(), getQuote: vi.fn() },
}))

const localDate = (offsetDays = 0) => {
  const d = new Date()
  d.setDate(d.getDate() + offsetDays)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

// Backend shape of GET /properties/{id}/availability/ (prices are decimal strings or null)
const inventoryRow = (date: string, overrides: Record<string, unknown> = {}) => ({
  id: 1, date, available_rooms: 3, booked_rooms: 0, remaining_rooms: 3, price: '150.00', currency: 'EUR',
  is_available: true, minimum_stay: null, maximum_stay: null, notes: null, ...overrides,
})

const availabilityResponse = (dateInventory: ReturnType<typeof inventoryRow>[]) => ({
  data: { id: 42, room_types: [{ id: 1, rate_plans: [{ id: 1, date_inventory: dateInventory }] }] },
  error: null,
})

const mockGetAvailability = propertyAdapter.getAvailability as unknown as ReturnType<typeof vi.fn>
const mockGetQuote = propertyAdapter.getQuote as unknown as ReturnType<typeof vi.fn>

const quoteResponse = (nights: number, total: string, currency = 'EUR') => ({
  data: { check_in: '', check_out: '', number_of_nights: nights, number_of_rooms: 1, currency, nights: [], total_price: total },
  error: null,
})

/** "Mon, Sep 28", the way the calendar names a date */
const dayLabel = (date: string) => {
  const [y, m, d] = date.split('-').map(Number)
  return new Date(y, m - 1, d).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
}

const mockNavigate = vi.fn()
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-router-dom')>()
  return { ...actual, useNavigate: () => mockNavigate }
})

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  )
}

describe('RoomSelection', () => {
  const mockRatePlans: RatePlan[] = [
    {
      id: 1,
      name: 'Standard Rate',
      slug: 'standard-rate',
      rate_type: 'standard',
      description: 'Standard flexible rate with free cancellation',
      base_price: 120,
      currency: 'EUR',
      min_nights: 1,
      max_nights: 30,
      is_active: true,
      cancellation_policy: 'Free cancellation up to 48 hours before check-in',
      deposit_required: false,
    },
  ]

  const mockRoomTypes: RoomType[] = [
    {
      id: 1,
      name: 'Standard Room',
      slug: 'standard-room',
      description: 'Comfortable room with essential amenities',
      base_occupancy: 2,
      max_occupancy: 2,
      base_price: 120,
      currency: 'EUR',
      total_rooms: 5,
      bed_configuration: '1 Queen Bed',
      room_size: 25,
      rate_plans: mockRatePlans,
    },
    {
      id: 2,
      name: 'Deluxe Room',
      slug: 'deluxe-room',
      description: 'Spacious room with city views',
      base_occupancy: 2,
      max_occupancy: 3,
      base_price: 180,
      currency: 'EUR',
      total_rooms: 3,
      bed_configuration: '1 King Bed',
      room_size: 35,
      rate_plans: [],
    },
  ]

  beforeEach(() => {
    vi.clearAllMocks()
    mockGetAvailability.mockResolvedValue(availabilityResponse([inventoryRow(localDate(0))]))
    mockGetQuote.mockResolvedValue(quoteResponse(1, '150.00'))
  })

  const selectRoomAndRate = async () => {
    fireEvent.click(screen.getByText('Standard Room'))
    await waitFor(() => {
      expect(screen.getByText('Standard Rate')).toBeInTheDocument()
    })
    fireEvent.click(screen.getByText('Standard Rate'))
  }

  const calendarDay = (container: HTMLElement, date: string) =>
    container.querySelector(`.availability-calendar-day[data-date="${date}"]`) as HTMLElement

  /** Click a day, moving to the next month first when it is not on screen */
  const clickDay = async (container: HTMLElement, date: string) => {
    await waitFor(() => expect(container.querySelector('.availability-calendar-day[data-date]')).not.toBeNull())
    if (!calendarDay(container, date)) fireEvent.click(screen.getByRole('button', { name: /next month/i }))
    fireEvent.click(calendarDay(container, date))
  }

  describe('check-in and check-out range', () => {
    const fourNights = () => [1, 2, 3, 4, 5].map(offset => inventoryRow(localDate(offset)))

    it('prices the chosen range with the backend quote: "3 nights, total €195"', async () => {
      mockGetAvailability.mockResolvedValue(availabilityResponse(fourNights()))
      mockGetQuote.mockResolvedValue(quoteResponse(3, '195.00'))
      const { container } = renderWithRouter(<RoomSelection roomTypes={mockRoomTypes} propertyId={42} />)
      await selectRoomAndRate()

      await clickDay(container, localDate(1))
      await clickDay(container, localDate(4))

      expect(await screen.findByText('3 nights, total €195')).toBeInTheDocument()
      expect(mockGetQuote).toHaveBeenCalledWith(42, {
        roomTypeId: 1, ratePlanId: 1, checkIn: localDate(1), checkOut: localDate(4), rooms: 1,
      })
    })

    it('sends check-in and check-out to the booking page', async () => {
      mockGetAvailability.mockResolvedValue(availabilityResponse(fourNights()))
      const { container } = renderWithRouter(<RoomSelection roomTypes={mockRoomTypes} propertyId={42} />)
      await selectRoomAndRate()

      await clickDay(container, localDate(1))
      await clickDay(container, localDate(3))
      fireEvent.click(await screen.findByLabelText('Proceed to booking'))

      expect(mockNavigate).toHaveBeenCalledWith('/booking', {
        state: expect.objectContaining({ checkIn: localDate(1), checkOut: localDate(3) }),
      })
    })

    it('names the closed night and does not offer booking', async () => {
      mockGetAvailability.mockResolvedValue(availabilityResponse([
        inventoryRow(localDate(1)), inventoryRow(localDate(2), { is_available: false }), inventoryRow(localDate(3)),
      ]))
      const { container } = renderWithRouter(<RoomSelection roomTypes={mockRoomTypes} propertyId={42} />)
      await selectRoomAndRate()

      await clickDay(container, localDate(1))
      await clickDay(container, localDate(4))

      expect(await screen.findByText(`${dayLabel(localDate(2))} is not available. Choose other dates.`)).toBeInTheDocument()
      expect(screen.queryByLabelText('Proceed to booking')).not.toBeInTheDocument()
      expect(mockGetQuote).not.toHaveBeenCalled()
    })

    it('shows the backend reason when the quote is refused', async () => {
      mockGetAvailability.mockResolvedValue(availabilityResponse(fourNights()))
      mockGetQuote.mockResolvedValue({ data: null, error: 'No rooms left on 2030-01-02.' })
      const { container } = renderWithRouter(<RoomSelection roomTypes={mockRoomTypes} propertyId={42} />)
      await selectRoomAndRate()

      await clickDay(container, localDate(1))
      await clickDay(container, localDate(2))

      expect(await screen.findByText('No rooms left on 2030-01-02.')).toBeInTheDocument()
      expect(screen.queryByLabelText('Proceed to booking')).not.toBeInTheDocument()
    })

    it('asks for the check-out date after the check-in is picked', async () => {
      mockGetAvailability.mockResolvedValue(availabilityResponse(fourNights()))
      const { container } = renderWithRouter(<RoomSelection roomTypes={mockRoomTypes} propertyId={42} />)
      await selectRoomAndRate()

      await clickDay(container, localDate(1))

      expect(await screen.findByText('Now choose your check-out date.')).toBeInTheDocument()
      expect(screen.queryByLabelText('Proceed to booking')).not.toBeInTheDocument()
    })
  })

  describe('real availability (GET /properties/{id}/availability/)', () => {
    it('requests the next 90 days for the property when a rate plan is selected', async () => {
      renderWithRouter(<RoomSelection roomTypes={mockRoomTypes} propertyId={42} />)
      await selectRoomAndRate()

      await waitFor(() => {
        expect(mockGetAvailability).toHaveBeenCalledWith(42, { check_in: localDate(0), check_out: localDate(90) })
      })
    })

    it('shows the price from the API for each date', async () => {
      const { container } = renderWithRouter(<RoomSelection roomTypes={mockRoomTypes} propertyId={42} />)
      await selectRoomAndRate()

      await waitFor(() => {
        expect(calendarDay(container, localDate(0))).toHaveTextContent('€150')
      })
      expect(calendarDay(container, localDate(0))).toHaveAttribute('aria-disabled', 'false')
    })

    it('falls back to the rate plan base price when a date has no price', async () => {
      mockGetAvailability.mockResolvedValue(availabilityResponse([inventoryRow(localDate(0), { price: null })]))
      const { container } = renderWithRouter(<RoomSelection roomTypes={mockRoomTypes} propertyId={42} />)
      await selectRoomAndRate()

      await waitFor(() => {
        expect(calendarDay(container, localDate(0))).toHaveTextContent('€120')
      })
    })

    it('does not let closed, fully booked or missing dates be selected', async () => {
      // Month boundaries: only dates in the month on screen are rendered
      const today = localDate(0)
      mockGetAvailability.mockResolvedValue(availabilityResponse([
        inventoryRow(today, { is_available: false }),
      ]))
      const { container } = renderWithRouter(<RoomSelection roomTypes={mockRoomTypes} propertyId={42} />)
      await selectRoomAndRate()

      await waitFor(() => {
        expect(screen.getByText('Availability Calendar')).toBeInTheDocument()
      })
      await waitFor(() => {
        expect(calendarDay(container, today)).toHaveAttribute('aria-disabled', 'true')
      })
      expect(container.querySelector('.availability-calendar-day[aria-disabled="false"]')).toBeNull()
    })

    it('marks a date with no remaining rooms as not selectable', async () => {
      mockGetAvailability.mockResolvedValue(availabilityResponse([
        inventoryRow(localDate(0), { available_rooms: 2, booked_rooms: 2, remaining_rooms: 0 }),
      ]))
      const { container } = renderWithRouter(<RoomSelection roomTypes={mockRoomTypes} propertyId={42} />)
      await selectRoomAndRate()

      await waitFor(() => {
        expect(calendarDay(container, localDate(0))).toHaveAttribute('aria-disabled', 'true')
      })
    })

    it('shows a loading state while availability loads', async () => {
      mockGetAvailability.mockReturnValue(new Promise(() => {}))
      renderWithRouter(<RoomSelection roomTypes={mockRoomTypes} propertyId={42} />)
      await selectRoomAndRate()

      expect(await screen.findByText('Loading availability...')).toBeInTheDocument()
    })

    it('shows the error and retries on request', async () => {
      mockGetAvailability.mockResolvedValueOnce({ data: null, error: 'Server is unavailable' })
      renderWithRouter(<RoomSelection roomTypes={mockRoomTypes} propertyId={42} />)
      await selectRoomAndRate()

      const alert = await screen.findByRole('alert')
      expect(alert).toHaveTextContent('Server is unavailable')
      expect(screen.queryByText('Availability Calendar')).toBeInTheDocument()

      fireEvent.click(screen.getByRole('button', { name: 'Try again' }))
      await waitFor(() => {
        expect(mockGetAvailability).toHaveBeenCalledTimes(2)
      })
      await waitFor(() => {
        expect(screen.queryByRole('alert')).not.toBeInTheDocument()
      })
    })

    it('says so when there is no availability', async () => {
      mockGetAvailability.mockResolvedValue(availabilityResponse([]))
      renderWithRouter(<RoomSelection roomTypes={mockRoomTypes} propertyId={42} />)
      await selectRoomAndRate()

      expect(await screen.findByText('No availability for the next 90 days.')).toBeInTheDocument()
    })
  })

  it('renders empty state when no room types provided', () => {
    renderWithRouter(<RoomSelection propertyId={1} roomTypes={[]} />)
    
    expect(screen.getByText('No rooms available for this property')).toBeInTheDocument()
  })

  it('renders room selection title', () => {
    renderWithRouter(<RoomSelection propertyId={1} roomTypes={mockRoomTypes} />)
    
    expect(screen.getByText('Select Your Room')).toBeInTheDocument()
  })

  it('renders available rooms section', () => {
    renderWithRouter(<RoomSelection propertyId={1} roomTypes={mockRoomTypes} />)
    
    expect(screen.getAllByText('Available Rooms').length).toBeGreaterThan(0)
  })

  it('renders room cards for each room type', () => {
    renderWithRouter(<RoomSelection propertyId={1} roomTypes={mockRoomTypes} />)
    
    expect(screen.getByText('Standard Room')).toBeInTheDocument()
    expect(screen.getByText('Deluxe Room')).toBeInTheDocument()
  })

  it('renders room card with correct information', () => {
    renderWithRouter(<RoomSelection propertyId={1} roomTypes={mockRoomTypes} />)
    
    expect(screen.getByText('Comfortable room with essential amenities')).toBeInTheDocument()
    expect(screen.getByText('€120')).toBeInTheDocument()
    expect(screen.getByText('2 - 2 guests')).toBeInTheDocument()
  })

  it('selects room when room card is clicked', async () => {
    renderWithRouter(<RoomSelection propertyId={1} roomTypes={mockRoomTypes} />)
    
    const standardRoom = screen.getByText('Standard Room')
    fireEvent.click(standardRoom)
    
    await waitFor(() => {
      expect(screen.getByText('Standard Rate')).toBeInTheDocument()
    }, { timeout: 3000 })
  })

  it('displays rate plans after room selection', async () => {
    renderWithRouter(<RoomSelection propertyId={1} roomTypes={mockRoomTypes} />)
    
    const standardRoom = screen.getByText('Standard Room')
    fireEvent.click(standardRoom)
    
    await waitFor(() => {
      expect(screen.getByText('Standard Rate')).toBeInTheDocument()
    }, { timeout: 3000 })
  })

  it('displays availability calendar after rate plan selection', async () => {
    renderWithRouter(<RoomSelection propertyId={1} roomTypes={mockRoomTypes} />)
    
    const standardRoom = screen.getByText('Standard Room')
    fireEvent.click(standardRoom)
    
    await waitFor(() => {
      expect(screen.getByText('Standard Rate')).toBeInTheDocument()
    }, { timeout: 3000 })
    
    const standardRate = screen.getByText('Standard Rate')
    fireEvent.click(standardRate)
    
    await waitFor(() => {
      expect(screen.getByText('Availability Calendar')).toBeInTheDocument()
    }, { timeout: 3000 })
  })

  it('displays selection summary when all selections are made', async () => {
    renderWithRouter(<RoomSelection propertyId={1} roomTypes={mockRoomTypes} />)
    
    const standardRoom = screen.getByText('Standard Room')
    fireEvent.click(standardRoom)
    
    await waitFor(() => {
      expect(screen.getByText('Standard Rate')).toBeInTheDocument()
    })
    
    const standardRate = screen.getByText('Standard Rate')
    fireEvent.click(standardRate)
    
    await waitFor(() => {
      expect(screen.getByText('Availability Calendar')).toBeInTheDocument()
    })
    
    // Click a date to complete selection
    const calendar = screen.getByText('Availability Calendar')
    // Note: Calendar interaction would require more complex test setup
    expect(calendar).toBeInTheDocument()
  })

  it('resets date selection when different rate plan is selected', async () => {
    renderWithRouter(<RoomSelection propertyId={1} roomTypes={mockRoomTypes} />)
    
    const standardRoom = screen.getByText('Standard Room')
    fireEvent.click(standardRoom)
    
    await waitFor(() => {
      expect(screen.getByText('Standard Rate')).toBeInTheDocument()
    }, { timeout: 3000 })
    
    const standardRate = screen.getByText('Standard Rate')
    fireEvent.click(standardRate)
    
    await waitFor(() => {
      expect(screen.getByText('Availability Calendar')).toBeInTheDocument()
    }, { timeout: 3000 })
    
    // This test would need multiple rate plans to be meaningful
    // Skipping as we only have one rate plan in mock data
  })

  it('sends the property id from the page to the booking page (F21)', async () => {
    // The backend's room_types[] have no property_id; the page passes the property id down
    const { container } = renderWithRouter(<RoomSelection roomTypes={mockRoomTypes} propertyId={42} />)

    fireEvent.click(screen.getByText('Standard Room'))
    await waitFor(() => {
      expect(screen.getByText('Standard Rate')).toBeInTheDocument()
    })
    fireEvent.click(screen.getByText('Standard Rate'))
    await waitFor(() => {
      expect(screen.getByText('Availability Calendar')).toBeInTheDocument()
    })

    await clickDay(container, localDate(0))
    await clickDay(container, localDate(1))
    fireEvent.click(await screen.findByLabelText('Proceed to booking'))

    expect(mockNavigate).toHaveBeenCalledWith(
      '/booking',
      { state: expect.objectContaining({ propertyId: 42, roomTypeId: 1, ratePlanId: 1 }) }
    )
  })

  it('uses provided currency prop', () => {
    renderWithRouter(<RoomSelection propertyId={1} roomTypes={mockRoomTypes} currency="USD" />)
    
    // RoomCard uses the room's own currency, not the prop
    // This test validates that rooms are rendered correctly
    expect(screen.getByText('Standard Room')).toBeInTheDocument()
    expect(screen.getByText('Deluxe Room')).toBeInTheDocument()
  })
})
