import { describe, it, expect, afterEach, vi } from 'vitest'
import { render, screen, fireEvent, act } from '@testing-library/react'
import { useTilt } from './useTilt'

function Card() {
  const ref = useTilt<HTMLDivElement>(10)
  return <div ref={ref} data-testid="card" />
}

function allowTilt(matches: boolean) {
  window.matchMedia = vi.fn().mockReturnValue({ matches }) as unknown as typeof window.matchMedia
}

/** jsdom has no PointerEvent; the hook only reads clientX and clientY */
const move = (element: HTMLElement, clientX: number, clientY: number) =>
  act(() => { element.dispatchEvent(new MouseEvent('pointermove', { clientX, clientY })) })

function sized(element: HTMLElement) {
  element.getBoundingClientRect = () => ({ left: 0, top: 0, width: 200, height: 100, right: 200, bottom: 100, x: 0, y: 0, toJSON: () => ({}) })
}

afterEach(() => { delete (window as { matchMedia?: unknown }).matchMedia })

describe('useTilt', () => {
  it('tilts towards the pointer and resets when it leaves', () => {
    allowTilt(true)
    render(<Card />)
    const card = screen.getByTestId('card')
    sized(card)

    move(card, 200, 0)
    expect(card.style.getPropertyValue('--tilt-y')).toBe('5.00deg')
    expect(card.style.getPropertyValue('--tilt-x')).toBe('5.00deg')

    fireEvent.pointerLeave(card)
    expect(card.style.getPropertyValue('--tilt-x')).toBe('')
    expect(card.style.getPropertyValue('--tilt-y')).toBe('')
  })

  it('does nothing on touch screens or with reduced motion', () => {
    allowTilt(false)
    render(<Card />)
    const card = screen.getByTestId('card')
    sized(card)

    move(card, 200, 0)
    expect(card.style.getPropertyValue('--tilt-y')).toBe('')
  })

  it('does nothing where matchMedia does not exist', () => {
    render(<Card />)
    const card = screen.getByTestId('card')
    sized(card)

    move(card, 200, 0)
    expect(card.style.getPropertyValue('--tilt-y')).toBe('')
  })
})
