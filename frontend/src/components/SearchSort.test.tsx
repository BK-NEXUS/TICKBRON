import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { SearchSort } from './SearchSort'

describe('SearchSort', () => {
  it('renders sort label and select', () => {
    const onSortChange = vi.fn()

    render(<SearchSort sortBy="relevance" onSortChange={onSortChange} />)

    expect(screen.getByText('Sort by:')).toBeInTheDocument()
    expect(screen.getByLabelText('Sort search results')).toBeInTheDocument()
  })

  it('renders all sort options', () => {
    const onSortChange = vi.fn()

    render(<SearchSort sortBy="relevance" onSortChange={onSortChange} />)

    const select = screen.getByLabelText('Sort search results')
    expect(select).toBeInTheDocument()

    const options = screen.getAllByRole('option')
    expect(options).toHaveLength(5)
    expect(screen.getByText('Relevance')).toBeInTheDocument()
    expect(screen.getByText('Price: Low to High')).toBeInTheDocument()
    expect(screen.getByText('Price: High to Low')).toBeInTheDocument()
    expect(screen.getByText('Rating')).toBeInTheDocument()
    expect(screen.getByText('Number of Reviews')).toBeInTheDocument()
  })

  it('displays current sort value', () => {
    const onSortChange = vi.fn()

    render(<SearchSort sortBy="price_low" onSortChange={onSortChange} />)

    const select = screen.getByLabelText('Sort search results') as HTMLSelectElement
    expect(select.value).toBe('price_low')
  })

  it('calls onSortChange when sort option changes', () => {
    const onSortChange = vi.fn()

    render(<SearchSort sortBy="relevance" onSortChange={onSortChange} />)

    const select = screen.getByLabelText('Sort search results')
    fireEvent.change(select, { target: { value: 'price_high' } })

    expect(onSortChange).toHaveBeenCalledWith('price_high')
  })

  it('has proper ARIA attributes', () => {
    const onSortChange = vi.fn()

    render(<SearchSort sortBy="relevance" onSortChange={onSortChange} />)

    const select = screen.getByLabelText('Sort search results')
    expect(select).toHaveAttribute('aria-label', 'Sort search results')
  })

  it('has proper label association', () => {
    const onSortChange = vi.fn()

    render(<SearchSort sortBy="relevance" onSortChange={onSortChange} />)

    const label = screen.getByText('Sort by:')
    const select = screen.getByLabelText('Sort search results')
    expect(label).toHaveAttribute('for', 'sort-select')
    expect(select).toHaveAttribute('id', 'sort-select')
  })
})
