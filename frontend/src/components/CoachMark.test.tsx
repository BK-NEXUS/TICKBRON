import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { CoachMark } from './CoachMark'

describe('CoachMark', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('renders when not shown before', () => {
    render(
      <CoachMark
        featureId="test-feature"
        title="Test Title"
        message="Test message"
      />
    )

    expect(screen.getByText('Test Title')).toBeInTheDocument()
    expect(screen.getByText('Test message')).toBeInTheDocument()
  })

  it('does not render when shown before with showOnce', () => {
    localStorage.setItem('coachmark-test-feature-shown', 'true')

    render(
      <CoachMark
        featureId="test-feature"
        title="Test Title"
        message="Test message"
        showOnce={true}
      />
    )

    expect(screen.queryByText('Test Title')).not.toBeInTheDocument()
  })

  it('renders when shown before but showOnce is false', () => {
    localStorage.setItem('coachmark-test-feature-shown', 'true')

    render(
      <CoachMark
        featureId="test-feature"
        title="Test Title"
        message="Test message"
        showOnce={false}
      />
    )

    // When showOnce is false, it should always render regardless of localStorage
    expect(screen.getByText('Test Title')).toBeInTheDocument()
  })

  it('closes when close button is clicked', () => {
    render(
      <CoachMark
        featureId="test-feature"
        title="Test Title"
        message="Test message"
      />
    )

    const closeButton = screen.getByLabelText('Close coach mark')
    fireEvent.click(closeButton)

    expect(screen.queryByText('Test Title')).not.toBeInTheDocument()
  })

  it('calls onClose callback when closed', () => {
    const onClose = vi.fn()

    render(
      <CoachMark
        featureId="test-feature"
        title="Test Title"
        message="Test message"
        onClose={onClose}
      />
    )

    const closeButton = screen.getByLabelText('Close coach mark')
    fireEvent.click(closeButton)

    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('saves to localStorage when closed with showOnce', () => {
    render(
      <CoachMark
        featureId="test-feature"
        title="Test Title"
        message="Test message"
        showOnce={true}
      />
    )

    const closeButton = screen.getByLabelText('Close coach mark')
    fireEvent.click(closeButton)

    expect(localStorage.getItem('coachmark-test-feature-shown')).toBe('true')
  })

  it('does not save to localStorage when showOnce is false', () => {
    render(
      <CoachMark
        featureId="test-feature"
        title="Test Title"
        message="Test message"
        showOnce={false}
      />
    )

    const closeButton = screen.getByLabelText('Close coach mark')
    fireEvent.click(closeButton)

    // When showOnce is false, it should not save to localStorage
    expect(localStorage.getItem('coachmark-test-feature-shown')).toBeNull()
  })

  it('has proper accessibility attributes', () => {
    render(
      <CoachMark
        featureId="test-feature"
        title="Test Title"
        message="Test message"
      />
    )

    const coachMark = screen.getByRole('dialog')
    expect(coachMark).toBeInTheDocument()
    expect(coachMark).toHaveAttribute('aria-labelledby', 'coachmark-title-test-feature')

    const title = screen.getByText('Test Title')
    expect(title).toHaveAttribute('id', 'coachmark-title-test-feature')
  })

  it('applies correct position class', () => {
    const { container } = render(
      <CoachMark
        featureId="test-feature"
        title="Test Title"
        message="Test message"
        position="bottom"
      />
    )

    const coachMark = container.querySelector('.coach-mark')
    expect(coachMark).toHaveClass('coach-mark--bottom')
  })
})
