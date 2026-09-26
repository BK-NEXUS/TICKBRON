import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { RouterProvider, createMemoryRouter, MemoryRouter, Routes, Route, useLocation } from 'react-router-dom'
import { SearchForm } from './SearchForm'

describe('SearchForm', () => {
  describe('optional dates (E2E BUG 1)', () => {
    const SearchResultsProbe = () => {
      const location = useLocation()
      return <div data-testid="search-query">Search results page {location.search}</div>
    }
    const renderWithSearchRoute = () =>
      render(
        <MemoryRouter initialEntries={['/']}>
          <Routes>
            <Route path="/" element={<SearchForm />} />
            <Route path="/search" element={<SearchResultsProbe />} />
          </Routes>
        </MemoryRouter>
      )

    it('searches by city without dates', async () => {
      renderWithSearchRoute()
      fireEvent.change(screen.getByLabelText('Destination'), { target: { value: 'Tashkent' } })
      fireEvent.click(screen.getByRole('button', { name: 'Search' }))

      const probe = await screen.findByTestId('search-query')
      const params = new URLSearchParams(probe.textContent?.split('Search results page ')[1] ?? '')
      expect(params.get('destination')).toBe('Tashkent')
      expect(params.has('check_in')).toBe(false)
      expect(params.has('check_out')).toBe(false)
    })

    it('asks for check-out when only check-in is given', async () => {
      renderWithSearchRoute()
      const future = new Date()
      future.setDate(future.getDate() + 5)
      fireEvent.change(screen.getByLabelText('Destination'), { target: { value: 'Tashkent' } })
      fireEvent.change(screen.getByLabelText('Check-in'), { target: { value: future.toISOString().split('T')[0] } })
      fireEvent.click(screen.getByRole('button', { name: 'Search' }))

      expect(await screen.findByText('Check-out date is required')).toBeInTheDocument()
      expect(screen.queryByTestId('search-query')).not.toBeInTheDocument()
    })
  })

  describe('date range picker', () => {
    const localDate = (offsetDays: number) => {
      const d = new Date()
      d.setDate(d.getDate() + offsetDays)
      return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
    }
    const clickDay = (container: HTMLElement, date: string) => {
      let day = container.querySelector(`[data-date="${date}"]`)
      if (!day) {
        fireEvent.click(screen.getByRole('button', { name: /next month/i }))
        day = container.querySelector(`[data-date="${date}"]`)
      }
      fireEvent.click(day as HTMLElement)
    }
    const renderForm = () => render(<BrowserRouter><SearchForm /></BrowserRouter>)

    it('clicking the check-in field opens a calendar; start then end fills both dates', () => {
      const { container } = renderForm()
      fireEvent.click(screen.getByLabelText('Check-in'))
      expect(screen.getByRole('dialog', { name: 'Choose your dates' })).toBeInTheDocument()

      clickDay(container, localDate(3))
      expect(screen.getByLabelText('Check-in')).toHaveValue(localDate(3))
      expect(screen.getByLabelText('Check-out')).toHaveValue('')

      clickDay(container, localDate(6))
      expect(screen.getByLabelText('Check-out')).toHaveValue(localDate(6))
      // Done: the calendar closes once the range is complete
      expect(screen.queryByRole('dialog', { name: 'Choose your dates' })).not.toBeInTheDocument()
    })

    it('highlights the chosen range when reopened', () => {
      const { container } = renderForm()
      fireEvent.click(screen.getByLabelText('Check-in'))
      clickDay(container, localDate(3))
      clickDay(container, localDate(6))
      fireEvent.click(screen.getByLabelText('Check-out'))

      const inRange = container.querySelector(`[data-date="${localDate(4)}"]`)
      if (inRange) expect(inRange).toHaveClass('availability-calendar-day--in-range')
      expect(container.querySelector('.availability-calendar-day--range-start, .availability-calendar-day--range-end'))
        .not.toBeNull()
    })

    it('past days cannot be picked', () => {
      const { container } = renderForm()
      fireEvent.click(screen.getByLabelText('Check-in'))
      const yesterday = container.querySelector(`[data-date="${localDate(-1)}"]`)
      if (yesterday) {
        expect(yesterday).toHaveAttribute('aria-disabled', 'true')
        fireEvent.click(yesterday)
        expect(screen.getByLabelText('Check-in')).toHaveValue('')
      }
    })

    it('can be closed without choosing', () => {
      renderForm()
      fireEvent.click(screen.getByLabelText('Check-out'))
      fireEvent.click(screen.getByRole('button', { name: 'Close calendar' }))
      expect(screen.queryByRole('dialog', { name: 'Choose your dates' })).not.toBeInTheDocument()
    })
  })

  const mockNavigate = vi.fn()

  beforeEach(() => {
    mockNavigate.mockClear()
  })

  it('renders the search form with all fields', () => {
    render(
      <BrowserRouter>
        <SearchForm />
      </BrowserRouter>
    )

    expect(screen.getByLabelText('Destination')).toBeInTheDocument()
    expect(screen.getByLabelText('Check-in')).toBeInTheDocument()
    expect(screen.getByLabelText('Check-out')).toBeInTheDocument()
    expect(screen.getByLabelText('Guests')).toBeInTheDocument()
    expect(screen.getByLabelText('Adults')).toBeInTheDocument()
    expect(screen.getByLabelText('Children')).toBeInTheDocument()
    expect(screen.getByLabelText('Rooms')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Search' })).toBeInTheDocument()
  })

  it('renders with default values', () => {
    render(
      <BrowserRouter>
        <SearchForm />
      </BrowserRouter>
    )

    const destinationInput = screen.getByLabelText('Destination') as HTMLInputElement
    const guestsInput = screen.getByLabelText('Guests') as HTMLInputElement
    const adultsInput = screen.getByLabelText('Adults') as HTMLInputElement
    const childrenInput = screen.getByLabelText('Children') as HTMLInputElement
    const roomsInput = screen.getByLabelText('Rooms') as HTMLInputElement

    expect(destinationInput.value).toBe('')
    expect(guestsInput.value).toBe('1')
    expect(adultsInput.value).toBe('1')
    expect(childrenInput.value).toBe('0')
    expect(roomsInput.value).toBe('1')
  })

  it('initializes form from URL parameters', () => {
    const router = createMemoryRouter(
      [
        {
          path: '/',
          element: <SearchForm />,
        },
      ],
      {
        initialEntries: ['/?destination=Paris&check_in=2024-01-15&check_out=2024-01-20&guests=2&adults=2&children=0&rooms=1'],
      }
    )

    render(<RouterProvider router={router} />)

    const destinationInput = screen.getByLabelText('Destination') as HTMLInputElement
    const checkInInput = screen.getByLabelText('Check-in') as HTMLInputElement
    const checkOutInput = screen.getByLabelText('Check-out') as HTMLInputElement
    const guestsInput = screen.getByLabelText('Guests') as HTMLInputElement
    const adultsInput = screen.getByLabelText('Adults') as HTMLInputElement
    const childrenInput = screen.getByLabelText('Children') as HTMLInputElement
    const roomsInput = screen.getByLabelText('Rooms') as HTMLInputElement

    expect(destinationInput.value).toBe('Paris')
    expect(checkInInput.value).toBe('2024-01-15')
    expect(checkOutInput.value).toBe('2024-01-20')
    expect(guestsInput.value).toBe('2')
    expect(adultsInput.value).toBe('2')
    expect(childrenInput.value).toBe('0')
    expect(roomsInput.value).toBe('1')
  })

  it('handles destination input change', () => {
    render(
      <BrowserRouter>
        <SearchForm />
      </BrowserRouter>
    )

    const destinationInput = screen.getByLabelText('Destination')
    fireEvent.change(destinationInput, { target: { value: 'Tokyo' } })

    expect((destinationInput as HTMLInputElement).value).toBe('Tokyo')
  })

  it('handles date input changes', () => {
    render(
      <BrowserRouter>
        <SearchForm />
      </BrowserRouter>
    )

    const checkInInput = screen.getByLabelText('Check-in')
    const checkOutInput = screen.getByLabelText('Check-out')

    fireEvent.change(checkInInput, { target: { value: '2024-02-01' } })
    fireEvent.change(checkOutInput, { target: { value: '2024-02-05' } })

    expect((checkInInput as HTMLInputElement).value).toBe('2024-02-01')
    expect((checkOutInput as HTMLInputElement).value).toBe('2024-02-05')
  })

  it('handles guest count changes', () => {
    render(
      <BrowserRouter>
        <SearchForm />
      </BrowserRouter>
    )

    const guestsInput = screen.getByLabelText('Guests')
    const adultsInput = screen.getByLabelText('Adults')
    const childrenInput = screen.getByLabelText('Children')
    const roomsInput = screen.getByLabelText('Rooms')

    fireEvent.change(guestsInput, { target: { value: '3' } })
    fireEvent.change(adultsInput, { target: { value: '2' } })
    fireEvent.change(childrenInput, { target: { value: '1' } })
    fireEvent.change(roomsInput, { target: { value: '2' } })

    expect((guestsInput as HTMLInputElement).value).toBe('3')
    expect((adultsInput as HTMLInputElement).value).toBe('2')
    expect((childrenInput as HTMLInputElement).value).toBe('1')
    expect((roomsInput as HTMLInputElement).value).toBe('2')
  })

  it('shows validation error for empty destination on blur', async () => {
    render(
      <BrowserRouter>
        <SearchForm />
      </BrowserRouter>
    )

    const destinationInput = screen.getByLabelText('Destination')
    fireEvent.blur(destinationInput)

    await waitFor(() => {
      expect(screen.getByText('Destination is required')).toBeInTheDocument()
    })
  })

  it('shows validation error for short destination on blur', async () => {
    render(
      <BrowserRouter>
        <SearchForm />
      </BrowserRouter>
    )

    const destinationInput = screen.getByLabelText('Destination')
    fireEvent.change(destinationInput, { target: { value: 'A' } })
    fireEvent.blur(destinationInput)

    await waitFor(() => {
      expect(screen.getByText('Destination must be at least 2 characters')).toBeInTheDocument()
    })
  })

  it('shows validation error for too long destination on blur', async () => {
    render(
      <BrowserRouter>
        <SearchForm />
      </BrowserRouter>
    )

    const destinationInput = screen.getByLabelText('Destination')
    const longDestination = 'A'.repeat(101)
    fireEvent.change(destinationInput, { target: { value: longDestination } })
    fireEvent.blur(destinationInput)

    await waitFor(() => {
      expect(screen.getByText('Destination must be less than 100 characters')).toBeInTheDocument()
    })
  })

  it('shows validation error for past check-in date on blur', async () => {
    render(
      <BrowserRouter>
        <SearchForm />
      </BrowserRouter>
    )

    const checkInInput = screen.getByLabelText('Check-in')
    const pastDate = '2020-01-01'
    fireEvent.change(checkInInput, { target: { value: pastDate } })
    fireEvent.blur(checkInInput)

    await waitFor(() => {
      expect(screen.getByText('Check-in date cannot be in the past')).toBeInTheDocument()
    })
  })

  it('shows validation error for check-out before check-in on blur', async () => {
    render(
      <BrowserRouter>
        <SearchForm />
      </BrowserRouter>
    )

    const checkInInput = screen.getByLabelText('Check-in')
    const checkOutInput = screen.getByLabelText('Check-out')

    fireEvent.change(checkInInput, { target: { value: '2024-02-05' } })
    fireEvent.change(checkOutInput, { target: { value: '2024-02-01' } })
    fireEvent.blur(checkOutInput)

    await waitFor(() => {
      expect(screen.getByText('Check-out date must be after check-in date')).toBeInTheDocument()
    })
  })

  it('shows validation error for guest composition mismatch', async () => {
    render(
      <BrowserRouter>
        <SearchForm />
      </BrowserRouter>
    )

    const guestsInput = screen.getByLabelText('Guests')

    fireEvent.change(guestsInput, { target: { value: '5' } })
    // Keep adults at default 1, so composition doesn't match

    const submitButton = screen.getByText('Search')
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('Total guests must equal adults + children')).toBeInTheDocument()
    })
  })

  it('shows validation error for negative children on blur', async () => {
    render(
      <BrowserRouter>
        <SearchForm />
      </BrowserRouter>
    )

    const childrenInput = screen.getByLabelText('Children')
    fireEvent.change(childrenInput, { target: { value: '-1' } })
    fireEvent.blur(childrenInput)

    await waitFor(() => {
      expect(screen.getByText('Children cannot be negative')).toBeInTheDocument()
    })
  })

  it('shows validation error for guest composition mismatch on blur', async () => {
    render(
      <BrowserRouter>
        <SearchForm />
      </BrowserRouter>
    )

    const guestsInput = screen.getByLabelText('Guests')
    const adultsInput = screen.getByLabelText('Adults')
    const childrenInput = screen.getByLabelText('Children')

    fireEvent.change(guestsInput, { target: { value: '5' } })
    fireEvent.change(adultsInput, { target: { value: '2' } })
    fireEvent.change(childrenInput, { target: { value: '1' } })
    fireEvent.blur(guestsInput)

    await waitFor(() => {
      expect(screen.getByText('Total guests must equal adults + children')).toBeInTheDocument()
    })
  })

  it('clears error when user starts typing', async () => {
    render(
      <BrowserRouter>
        <SearchForm />
      </BrowserRouter>
    )

    const destinationInput = screen.getByLabelText('Destination')
    fireEvent.blur(destinationInput)

    await waitFor(() => {
      expect(screen.getByText('Destination is required')).toBeInTheDocument()
    })

    fireEvent.change(destinationInput, { target: { value: 'Paris' } })

    await waitFor(() => {
      expect(screen.queryByText('Destination is required')).not.toBeInTheDocument()
    })
  })

  it('prevents form submission with validation errors', async () => {
    const router = createMemoryRouter(
      [
        {
          path: '/',
          element: <SearchForm />,
        },
      ],
      {
        initialEntries: ['/'],
      }
    )

    render(<RouterProvider router={router} />)

    const submitButton = screen.getByRole('button', { name: 'Search' })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('Destination is required')).toBeInTheDocument()
    })
  })

  it('has proper accessibility attributes', () => {
    render(
      <BrowserRouter>
        <SearchForm />
      </BrowserRouter>
    )

    const destinationInput = screen.getByLabelText('Destination')
    expect(destinationInput).toHaveAttribute('type', 'text')
    expect(destinationInput).toHaveAttribute('aria-invalid', 'false')

    const checkInInput = screen.getByLabelText('Check-in')
    expect(checkInInput).toHaveAttribute('type', 'date')

    const checkOutInput = screen.getByLabelText('Check-out')
    expect(checkOutInput).toHaveAttribute('type', 'date')

    const guestsInput = screen.getByLabelText('Guests')
    expect(guestsInput).toHaveAttribute('type', 'number')
    expect(guestsInput).toHaveAttribute('min', '1')
    expect(guestsInput).toHaveAttribute('max', '50')
  })

  it('updates aria-invalid attribute when validation fails', async () => {
    render(
      <BrowserRouter>
        <SearchForm />
      </BrowserRouter>
    )

    const destinationInput = screen.getByLabelText('Destination')
    fireEvent.blur(destinationInput)

    await waitFor(() => {
      expect(destinationInput).toHaveAttribute('aria-invalid', 'true')
    })
  })

  it('handles malformed URL parameters gracefully', () => {
    const router = createMemoryRouter(
      [
        {
          path: '/',
          element: <SearchForm />,
        },
      ],
      {
        initialEntries: ['/?destination=Test&guests=invalid&adults=abc'],
      }
    )

    render(<RouterProvider router={router} />)

    const destinationInput = screen.getByLabelText('Destination') as HTMLInputElement
    const guestsInput = screen.getByLabelText('Guests') as HTMLInputElement
    const adultsInput = screen.getByLabelText('Adults') as HTMLInputElement

    expect(destinationInput.value).toBe('Test')
    // Invalid parseInt results in NaN, which falls back to default value of 1
    expect(guestsInput.value).toBe('1')
    expect(adultsInput.value).toBe('1')
  })

  it('handles missing URL parameters gracefully', () => {
    const router = createMemoryRouter(
      [
        {
          path: '/',
          element: <SearchForm />,
        },
      ],
      {
        initialEntries: ['/?destination=Paris'],
      }
    )

    render(<RouterProvider router={router} />)

    const destinationInput = screen.getByLabelText('Destination') as HTMLInputElement
    const checkInInput = screen.getByLabelText('Check-in') as HTMLInputElement
    const guestsInput = screen.getByLabelText('Guests') as HTMLInputElement

    expect(destinationInput.value).toBe('Paris')
    expect(checkInInput.value).toBe('') // Empty for missing params
    expect(guestsInput.value).toBe('1') // Default value
  })

  it('has proper form structure with semantic HTML', () => {
    render(
      <BrowserRouter>
        <SearchForm />
      </BrowserRouter>
    )

    const form = screen.getByText('Search').closest('form')
    expect(form).toBeInTheDocument()
    expect(form).toHaveClass('search-form')
  })

  it('maintains proper input field hierarchy', () => {
    render(
      <BrowserRouter>
        <SearchForm />
      </BrowserRouter>
    )

    const destinationLabel = screen.getByLabelText('Destination')
    const destinationInput = screen.getByLabelText('Destination')
    
    expect(destinationLabel).toBeInTheDocument()
    expect(destinationInput).toBeInTheDocument()
  })
})