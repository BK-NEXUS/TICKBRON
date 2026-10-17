import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { LocationPicker } from './LocationPicker'
import { I18nProvider } from '../i18n/I18nContext'

// jsdom has no layout: give the map a size so a click lands on a real coordinate
const sizes = { clientWidth: 400, clientHeight: 300 }
let originalWidth: PropertyDescriptor | undefined
let originalHeight: PropertyDescriptor | undefined

beforeEach(() => {
  localStorage.setItem('tickbron.language', 'en')
  originalWidth = Object.getOwnPropertyDescriptor(HTMLElement.prototype, 'clientWidth')
  originalHeight = Object.getOwnPropertyDescriptor(HTMLElement.prototype, 'clientHeight')
  Object.defineProperty(HTMLElement.prototype, 'clientWidth', { configurable: true, get: () => sizes.clientWidth })
  Object.defineProperty(HTMLElement.prototype, 'clientHeight', { configurable: true, get: () => sizes.clientHeight })
})

afterEach(() => {
  if (originalWidth) Object.defineProperty(HTMLElement.prototype, 'clientWidth', originalWidth)
  if (originalHeight) Object.defineProperty(HTMLElement.prototype, 'clientHeight', originalHeight)
  localStorage.clear()
})

const renderPicker = (value: { lat: number; lng: number } | null, onChange = vi.fn()) => {
  const view = render(<I18nProvider><LocationPicker value={value} onChange={onChange} /></I18nProvider>)
  return { ...view, onChange }
}

describe('LocationPicker', () => {
  it('shows the map with the hint and no pin while no location is set', () => {
    const { container } = renderPicker(null)
    expect(screen.getByRole('region', { name: 'Map: choose the property location' })).toBeInTheDocument()
    expect(screen.getByText(/Click the map or drag the pin/)).toBeInTheDocument()
    expect(container.querySelectorAll('.leaflet-marker-icon')).toHaveLength(0)
    expect(screen.queryByRole('button', { name: 'Remove location' })).toBeNull()
  })

  it('shows a pin where the location is', () => {
    const { container } = renderPicker({ lat: 41.311081, lng: 69.279737 })
    expect(container.querySelectorAll('.leaflet-marker-icon')).toHaveLength(1)
  })

  it('clicking the map sets the location, rounded to 6 decimals', () => {
    const { container, onChange } = renderPicker(null)
    fireEvent.click(container.querySelector('.leaflet-container') as HTMLElement, { clientX: 200, clientY: 150 })
    expect(onChange).toHaveBeenCalledTimes(1)
    const point = onChange.mock.calls[0][0]
    expect(point.lat).toBeCloseTo(41.3, 0)
    expect(point.lng).toBeCloseTo(64.6, 0)
    expect(String(point.lat).split('.')[1]?.length ?? 0).toBeLessThanOrEqual(6)
  })

  it('moves the pin when the value changes from outside (typed coordinates)', () => {
    const { container, rerender } = renderPicker({ lat: 41, lng: 69 })
    const pin = () => container.querySelector('.leaflet-marker-icon') as HTMLElement
    expect(pin()).toHaveAttribute('title', 'Property location: 41, 69')
    rerender(<I18nProvider><LocationPicker value={{ lat: 39.65, lng: 66.97 }} onChange={vi.fn()} /></I18nProvider>)
    expect(pin()).toHaveAttribute('title', 'Property location: 39.65, 66.97')
  })

  it('removes the pin when the value is cleared', () => {
    const { container, rerender } = renderPicker({ lat: 41, lng: 69 })
    rerender(<I18nProvider><LocationPicker value={null} onChange={vi.fn()} /></I18nProvider>)
    expect(container.querySelectorAll('.leaflet-marker-icon')).toHaveLength(0)
  })

  it('Remove location clears the value', () => {
    const { onChange } = renderPicker({ lat: 41, lng: 69 })
    fireEvent.click(screen.getByRole('button', { name: 'Remove location' }))
    expect(onChange).toHaveBeenCalledWith(null)
  })
})
