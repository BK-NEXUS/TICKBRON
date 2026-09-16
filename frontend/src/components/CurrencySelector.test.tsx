import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { CurrencySelector } from './CurrencySelector'

describe('CurrencySelector', () => {
  it('renders the current currency', () => {
    render(<CurrencySelector currentCurrency="USD" />)
    expect(screen.getByText('USD')).toBeInTheDocument()
    expect(screen.getByText('$')).toBeInTheDocument()
  })

  it('opens dropdown when button is clicked', () => {
    render(<CurrencySelector currentCurrency="USD" />)
    const button = screen.getByRole('button')
    fireEvent.click(button)
    expect(screen.getByText('Euro')).toBeInTheDocument()
    expect(screen.getByText('British Pound')).toBeInTheDocument()
  })

  it('calls onCurrencyChange when a currency is selected', () => {
    const handleChange = vi.fn()
    render(<CurrencySelector currentCurrency="USD" onCurrencyChange={handleChange} />)
    
    const button = screen.getByRole('button')
    fireEvent.click(button)
    
    const euroOption = screen.getByText('Euro')
    fireEvent.click(euroOption)
    
    expect(handleChange).toHaveBeenCalledWith('EUR')
  })

  it('closes dropdown after selection', () => {
    render(<CurrencySelector currentCurrency="USD" />)
    const button = screen.getByRole('button')
    fireEvent.click(button)
    
    const euroOption = screen.getByText('Euro')
    fireEvent.click(euroOption)
    
    expect(screen.queryByText('Euro')).not.toBeInTheDocument()
  })

  it('shows checkmark for selected currency', () => {
    render(<CurrencySelector currentCurrency="USD" />)
    const button = screen.getByRole('button')
    fireEvent.click(button)
    
    expect(screen.getByText('✓')).toBeInTheDocument()
  })

  it('applies custom className', () => {
    const { container } = render(
      <CurrencySelector currentCurrency="USD" className="custom-class" />
    )
    expect(container.firstChild).toHaveClass('custom-class')
  })
})
