import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { CurrencySelector } from './CurrencySelector'

describe('CurrencySelector', () => {
  it('renders the current currency', () => {
    render(<CurrencySelector currentCurrency="USD" />)
    expect(screen.getByText('USD')).toBeInTheDocument()
  })

  it('names the button after the current currency', () => {
    render(<CurrencySelector currentCurrency="UZS" />)
    expect(screen.getByRole('button', { name: 'Currency: Uzbek sum' })).toBeInTheDocument()
  })

  it('offers exactly UZS and USD', () => {
    render(<CurrencySelector currentCurrency="UZS" />)
    fireEvent.click(screen.getByRole('button'))
    expect(screen.getByText('Uzbek sum')).toBeInTheDocument()
    expect(screen.getByText('US dollar')).toBeInTheDocument()
    expect(screen.queryByText('Euro')).not.toBeInTheDocument()
  })

  it('calls onCurrencyChange when a currency is selected', () => {
    const handleChange = vi.fn()
    render(<CurrencySelector currentCurrency="UZS" onCurrencyChange={handleChange} />)
    fireEvent.click(screen.getByRole('button'))
    fireEvent.click(screen.getByText('US dollar'))
    expect(handleChange).toHaveBeenCalledWith('USD')
  })

  it('closes the dropdown after selection', () => {
    render(<CurrencySelector currentCurrency="UZS" />)
    fireEvent.click(screen.getByRole('button'))
    fireEvent.click(screen.getByText('US dollar'))
    expect(screen.queryByText('Uzbek sum')).not.toBeInTheDocument()
  })

  it('marks the selected currency', () => {
    render(<CurrencySelector currentCurrency="UZS" />)
    fireEvent.click(screen.getByRole('button'))
    expect(screen.getByText('Uzbek sum').closest('button')).toHaveAttribute('aria-current', 'true')
  })

  it('applies custom className', () => {
    const { container } = render(<CurrencySelector currentCurrency="USD" className="custom-class" />)
    expect(container.firstChild).toHaveClass('custom-class')
  })
})
