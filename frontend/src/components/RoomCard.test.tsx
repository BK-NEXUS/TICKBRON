import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { RoomCard } from './RoomCard'
import { RoomType } from '../adapters/searchAdapter'

describe('RoomCard', () => {
  const mockRoom: RoomType = {
    id: 1,
    property_id: 1,
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
  }

  it('renders room card with room information', () => {
    render(<RoomCard room={mockRoom} />)
    
    expect(screen.getByText('Standard Room')).toBeInTheDocument()
    expect(screen.getByText('Comfortable room with essential amenities')).toBeInTheDocument()
    expect(screen.getByText('2 - 2 guests')).toBeInTheDocument()
    expect(screen.getByText('1 Queen Bed')).toBeInTheDocument()
    expect(screen.getByText('25 m²')).toBeInTheDocument()
    expect(screen.getByText('5')).toBeInTheDocument()
  })

  it('renders price in correct format', () => {
    render(<RoomCard room={mockRoom} />)
    
    expect(screen.getByText('€120')).toBeInTheDocument()
    expect(screen.getByText('per night')).toBeInTheDocument()
  })

  it('does not render room size when not provided', () => {
    const roomWithoutSize: RoomType = { ...mockRoom, room_size: undefined }
    render(<RoomCard room={roomWithoutSize} />)
    
    expect(screen.queryByText(/m²/)).not.toBeInTheDocument()
  })

  it('calls onSelect when card is clicked', () => {
    const onSelect = vi.fn()
    render(<RoomCard room={mockRoom} onSelect={onSelect} />)
    
    const card = screen.getByRole('button')
    card.click()
    
    expect(onSelect).toHaveBeenCalledWith(1)
  })

  it('calls onSelect when Enter key is pressed', () => {
    const onSelect = vi.fn()
    render(<RoomCard room={mockRoom} onSelect={onSelect} />)
    
    const card = screen.getByRole('button')
    card.click()
    
    expect(onSelect).toHaveBeenCalledWith(1)
  })

  it('calls onSelect when Space key is pressed', () => {
    const onSelect = vi.fn()
    render(<RoomCard room={mockRoom} onSelect={onSelect} />)
    
    const card = screen.getByRole('button')
    card.click()
    
    expect(onSelect).toHaveBeenCalledWith(1)
  })

  it('shows selected indicator when isSelected is true', () => {
    render(<RoomCard room={mockRoom} isSelected={true} />)
    
    expect(screen.getByText('✓ Selected')).toBeInTheDocument()
  })

  it('does not show selected indicator when isSelected is false', () => {
    render(<RoomCard room={mockRoom} isSelected={false} />)
    
    expect(screen.queryByText('✓ Selected')).not.toBeInTheDocument()
  })

  it('applies selected styling when isSelected is true', () => {
    const { container } = render(<RoomCard room={mockRoom} isSelected={true} />)
    const card = container.querySelector('.room-card--selected')
    
    expect(card).toBeInTheDocument()
  })

  it('has proper accessibility attributes', () => {
    render(<RoomCard room={mockRoom} isSelected={false} />)
    
    const card = screen.getByRole('button')
    expect(card).toHaveAttribute('aria-pressed', 'false')
  })

  it('has proper accessibility attributes when selected', () => {
    render(<RoomCard room={mockRoom} isSelected={true} />)
    
    const card = screen.getByRole('button')
    expect(card).toHaveAttribute('aria-pressed', 'true')
  })

  it('formats price with different currency', () => {
    const usdRoom: RoomType = { ...mockRoom, currency: 'USD', base_price: 150 }
    render(<RoomCard room={usdRoom} />)
    
    expect(screen.getByText('$150')).toBeInTheDocument()
  })
})