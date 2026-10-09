import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { LanguageSelector } from './LanguageSelector'

describe('LanguageSelector', () => {
  it('renders the current language with an SVG flag, not an emoji', () => {
    const { container } = render(<LanguageSelector currentLanguage="en" />)
    expect(screen.getByText('EN')).toBeInTheDocument()
    expect(container.querySelector('button svg.flag-icon')).not.toBeNull()
  })

  it('names the button after the current language', () => {
    render(<LanguageSelector currentLanguage="ru" />)
    expect(screen.getByRole('button', { name: 'Language: Русский' })).toBeInTheDocument()
  })

  it('offers exactly Uzbek, Russian and English', () => {
    render(<LanguageSelector currentLanguage="en" />)
    fireEvent.click(screen.getByRole('button'))
    expect(screen.getAllByRole('button').slice(1).map((b) => b.textContent)).toEqual(["O'zbekcha", 'Русский', 'English'])
  })

  it('calls onLanguageChange when a language is selected', () => {
    const handleChange = vi.fn()
    render(<LanguageSelector currentLanguage="en" onLanguageChange={handleChange} />)
    fireEvent.click(screen.getByRole('button'))
    fireEvent.click(screen.getByText('Русский'))
    expect(handleChange).toHaveBeenCalledWith('ru')
  })

  it('closes the dropdown after selection', () => {
    render(<LanguageSelector currentLanguage="en" />)
    fireEvent.click(screen.getByRole('button'))
    fireEvent.click(screen.getByText('Русский'))
    expect(screen.queryByText("O'zbekcha")).not.toBeInTheDocument()
  })

  it('marks the selected language', () => {
    render(<LanguageSelector currentLanguage="en" />)
    fireEvent.click(screen.getByRole('button'))
    expect(screen.getByText('English').closest('button')).toHaveAttribute('aria-current', 'true')
  })

  it('applies custom className', () => {
    const { container } = render(<LanguageSelector currentLanguage="en" className="custom-class" />)
    expect(container.firstChild).toHaveClass('custom-class')
  })
})
