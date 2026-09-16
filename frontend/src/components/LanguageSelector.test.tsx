import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { LanguageSelector } from './LanguageSelector'

describe('LanguageSelector', () => {
  it('renders the current language', () => {
    render(<LanguageSelector currentLanguage="en" />)
    expect(screen.getByText('EN')).toBeInTheDocument()
    expect(screen.getByText('🇺🇸')).toBeInTheDocument()
  })

  it('opens dropdown when button is clicked', () => {
    render(<LanguageSelector currentLanguage="en" />)
    const button = screen.getByRole('button')
    fireEvent.click(button)
    expect(screen.getByText('Español')).toBeInTheDocument()
    expect(screen.getByText('Français')).toBeInTheDocument()
  })

  it('calls onLanguageChange when a language is selected', () => {
    const handleChange = vi.fn()
    render(<LanguageSelector currentLanguage="en" onLanguageChange={handleChange} />)
    
    const button = screen.getByRole('button')
    fireEvent.click(button)
    
    const spanishOption = screen.getByText('Español')
    fireEvent.click(spanishOption)
    
    expect(handleChange).toHaveBeenCalledWith('es')
  })

  it('closes dropdown after selection', () => {
    render(<LanguageSelector currentLanguage="en" />)
    const button = screen.getByRole('button')
    fireEvent.click(button)
    
    const spanishOption = screen.getByText('Español')
    fireEvent.click(spanishOption)
    
    expect(screen.queryByText('Español')).not.toBeInTheDocument()
  })

  it('shows checkmark for selected language', () => {
    render(<LanguageSelector currentLanguage="en" />)
    const button = screen.getByRole('button')
    fireEvent.click(button)
    
    expect(screen.getByText('✓')).toBeInTheDocument()
  })

  it('applies custom className', () => {
    const { container } = render(
      <LanguageSelector currentLanguage="en" className="custom-class" />
    )
    expect(container.firstChild).toHaveClass('custom-class')
  })
})
