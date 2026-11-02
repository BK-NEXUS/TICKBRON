import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { ErrorBoundary } from './ErrorBoundary'

function Boom(): never {
  throw new Error('webgl failed')
}

describe('ErrorBoundary', () => {
  it('shows the fallback when a child throws', () => {
    vi.spyOn(console, 'error').mockImplementation(() => {})
    render(
      <ErrorBoundary fallback={<p>fallback</p>}>
        <Boom />
      </ErrorBoundary>,
    )
    expect(screen.getByText('fallback')).toBeInTheDocument()
  })

  it('renders children when nothing throws', () => {
    render(
      <ErrorBoundary fallback={<p>fallback</p>}>
        <p>ok</p>
      </ErrorBoundary>,
    )
    expect(screen.getByText('ok')).toBeInTheDocument()
  })
})
