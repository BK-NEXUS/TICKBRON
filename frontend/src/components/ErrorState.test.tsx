import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { ErrorState } from './ErrorState'
import { I18nProvider } from '../i18n/I18nContext'

function show(props: Partial<React.ComponentProps<typeof ErrorState>> = {}, language = 'en') {
  localStorage.setItem('tickbron.language', language)
  return render(
    <I18nProvider><MemoryRouter><ErrorState message="Could not load your bookings." {...props} /></MemoryRouter></I18nProvider>,
  )
}

describe('ErrorState', () => {
  beforeEach(() => localStorage.clear())

  it('tells the visitor what happened, in an alert with a title and an icon that screen readers skip', () => {
    const { container } = show()
    const alert = screen.getByRole('alert')
    expect(alert).toHaveTextContent('Something went wrong')
    expect(alert).toHaveTextContent('Could not load your bookings.')
    expect(screen.getByRole('heading', { level: 2, name: 'Something went wrong' })).toBeInTheDocument()
    expect(container.querySelector('.empty-state-icon')).toHaveAttribute('aria-hidden', 'true')
  })

  it('takes its own title and can be the one heading of a whole page', () => {
    show({ title: 'Property not found', headingLevel: 1 })
    expect(screen.getByRole('heading', { level: 1, name: 'Property not found' })).toBeInTheDocument()
  })

  it('offers "Try Again" only when there is something to try again', () => {
    const { unmount } = show()
    expect(screen.queryByRole('button', { name: 'Try Again' })).not.toBeInTheDocument()
    unmount()
    const onRetry = vi.fn()
    show({ onRetry })
    fireEvent.click(screen.getByRole('button', { name: 'Try Again' }))
    expect(onRetry).toHaveBeenCalledTimes(1)
  })

  it('can offer a way out: a button with its own label and accessible name, or a link', () => {
    const onCta = vi.fn()
    const { unmount } = show({ ctaText: 'Back to search', ctaLabel: 'Go back to the search results', onCta })
    fireEvent.click(screen.getByRole('button', { name: 'Go back to the search results' }))
    expect(onCta).toHaveBeenCalled()
    unmount()
    show({ ctaText: 'Go Home', ctaLink: '/' })
    expect(screen.getByRole('link', { name: 'Go Home' })).toHaveAttribute('href', '/')
  })

  it.each(['uz', 'ru'])('says the default title in %s', language => {
    show({}, language)
    expect(screen.getByRole('alert')).not.toHaveTextContent('Something went wrong')
    expect(screen.getByRole('heading', { level: 2 }).textContent).toBeTruthy()
  })
})
