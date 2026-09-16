import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ListViewMapView } from './ListViewMapView'

describe('ListViewMapView', () => {
  it('renders list and map buttons', () => {
    const onViewChange = vi.fn()

    render(<ListViewMapView view="list" onViewChange={onViewChange} />)

    expect(screen.getByLabelText('List view')).toBeInTheDocument()
    expect(screen.getByLabelText('Map view')).toBeInTheDocument()
  })

  it('displays list button as active when view is list', () => {
    const onViewChange = vi.fn()

    render(<ListViewMapView view="list" onViewChange={onViewChange} />)

    const listButton = screen.getByLabelText('List view')
    expect(listButton).toHaveClass('list-view-map-view-button-active')
  })

  it('displays map button as active when view is map', () => {
    const onViewChange = vi.fn()

    render(<ListViewMapView view="map" onViewChange={onViewChange} />)

    const mapButton = screen.getByLabelText('Map view')
    expect(mapButton).toHaveClass('list-view-map-view-button-active')
  })

  it('calls onViewChange with list when list button is clicked', () => {
    const onViewChange = vi.fn()

    render(<ListViewMapView view="map" onViewChange={onViewChange} />)

    const listButton = screen.getByLabelText('List view')
    fireEvent.click(listButton)

    expect(onViewChange).toHaveBeenCalledWith('list')
  })

  it('calls onViewChange with map when map button is clicked', () => {
    const onViewChange = vi.fn()

    render(<ListViewMapView view="list" onViewChange={onViewChange} />)

    const mapButton = screen.getByLabelText('Map view')
    fireEvent.click(mapButton)

    expect(onViewChange).toHaveBeenCalledWith('map')
  })

  it('has proper ARIA attributes for list button', () => {
    const onViewChange = vi.fn()

    render(<ListViewMapView view="list" onViewChange={onViewChange} />)

    const listButton = screen.getByLabelText('List view')
    expect(listButton).toHaveAttribute('aria-pressed', 'true')
  })

  it('has proper ARIA attributes for map button', () => {
    const onViewChange = vi.fn()

    render(<ListViewMapView view="list" onViewChange={onViewChange} />)

    const mapButton = screen.getByLabelText('Map view')
    expect(mapButton).toHaveAttribute('aria-pressed', 'false')
  })

  it('has proper role for the container', () => {
    const onViewChange = vi.fn()

    render(<ListViewMapView view="list" onViewChange={onViewChange} />)

    const container = screen.getByRole('group')
    expect(container).toHaveAttribute('aria-label', 'View mode')
  })

  it('displays icons for both buttons', () => {
    const onViewChange = vi.fn()

    render(<ListViewMapView view="list" onViewChange={onViewChange} />)

    expect(screen.getByText('📋')).toBeInTheDocument()
    expect(screen.getByText('🗺️')).toBeInTheDocument()
  })

  it('displays labels for both buttons', () => {
    const onViewChange = vi.fn()

    render(<ListViewMapView view="list" onViewChange={onViewChange} />)

    expect(screen.getByText('List')).toBeInTheDocument()
    expect(screen.getByText('Map')).toBeInTheDocument()
  })
})
