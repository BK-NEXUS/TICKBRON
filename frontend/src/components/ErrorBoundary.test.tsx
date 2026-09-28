import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ErrorBoundary } from './ErrorBoundary'

// Component that throws an error
function ThrowError() {
  throw new Error('Test error')
}

describe('ErrorBoundary', () => {
  it('renders children when there is no error', () => {
    render(
      <ErrorBoundary>
        <div>Test content</div>
      </ErrorBoundary>
    )

    expect(screen.getByText('Test content')).toBeInTheDocument()
  })

  it('renders fallback UI when an error is thrown', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    )

    expect(screen.getByText('Something went wrong')).toBeInTheDocument()
    expect(screen.getByText('Refresh Page')).toBeInTheDocument()

    consoleSpy.mockRestore()
  })

  it('renders custom fallback when provided', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

    render(
      <ErrorBoundary fallback={<div>Custom error fallback</div>}>
        <ThrowError />
      </ErrorBoundary>
    )

    expect(screen.getByText('Custom error fallback')).toBeInTheDocument()
    expect(screen.queryByText('Something went wrong')).not.toBeInTheDocument()

    consoleSpy.mockRestore()
  })

  it('refreshes page when refresh button is clicked', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    // Mock window.location.reload using Object.defineProperty
    const locationDescriptor = Object.getOwnPropertyDescriptor(window, 'location')
    let reloadCalled = false
    const mockLocation = { reload: () => { reloadCalled = true } }
    Object.defineProperty(window, 'location', {
      value: mockLocation,
      writable: true,
      configurable: true,
    })

    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    )

    const refreshButton = screen.getByText('Refresh Page')
    fireEvent.click(refreshButton)

    expect(reloadCalled).toBe(true)

    consoleSpy.mockRestore()
    // Restore original location
    if (locationDescriptor) {
      Object.defineProperty(window, 'location', locationDescriptor)
    }
  })

  it('logs error to console in development', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    const originalEnv = import.meta.env.DEV

    // Mock DEV environment
    Object.defineProperty(import.meta, 'env', {
      value: { DEV: true },
      writable: true,
    })

    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    )

    expect(consoleSpy).toHaveBeenCalled()

    consoleSpy.mockRestore()
    
    // Restore original environment
    Object.defineProperty(import.meta, 'env', {
      value: { DEV: originalEnv },
      writable: true,
    })
  })
})
