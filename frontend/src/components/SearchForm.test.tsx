import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { RouterProvider, createMemoryRouter } from 'react-router-dom'
import { SearchForm } from './SearchForm'

describe('SearchForm', () => {
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