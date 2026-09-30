import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { PropertyRegionField } from './PropertyRegionField'
import { statusAdapter } from '../adapters/statusAdapter'

vi.mock('../adapters/statusAdapter', () => ({
  statusAdapter: { setPropertyRegion: vi.fn() },
}))

const setRegion = vi.mocked(statusAdapter.setPropertyRegion)

describe('PropertyRegionField', () => {
  beforeEach(() => vi.resetAllMocks())

  it('shows the current region, or Unspecified', () => {
    const { rerender } = render(<PropertyRegionField propertyId={1} region="Tashkent" />)
    expect(screen.getByLabelText('Region')).toHaveValue('Tashkent')

    rerender(<PropertyRegionField propertyId={2} region={null} />)
    expect(screen.getByLabelText('Region')).toHaveValue('')
    expect(screen.getByLabelText('Region')).toHaveAttribute('placeholder', 'Unspecified')
  })

  it('saves the region', async () => {
    setRegion.mockResolvedValue({ data: { id: 1, state: 'Samarkand' }, error: null })
    const onSaved = vi.fn()
    render(<PropertyRegionField propertyId={1} region={null} onSaved={onSaved} />)

    fireEvent.change(screen.getByLabelText('Region'), { target: { value: ' Samarkand ' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save region' }))

    expect(await screen.findByRole('status')).toHaveTextContent('Region saved')
    expect(setRegion).toHaveBeenCalledWith(1, 'Samarkand')
    expect(onSaved).toHaveBeenCalledWith('Samarkand')
    expect(screen.getByLabelText('Region')).toHaveValue('Samarkand')
  })

  it('Save is disabled until the region changes', () => {
    render(<PropertyRegionField propertyId={1} region="Tashkent" />)
    expect(screen.getByRole('button', { name: 'Save region' })).toBeDisabled()
  })

  it('shows the server error', async () => {
    setRegion.mockResolvedValue({ data: null, error: 'Ensure this field has no more than 100 characters.' })
    render(<PropertyRegionField propertyId={1} region="Tashkent" />)

    fireEvent.change(screen.getByLabelText('Region'), { target: { value: 'x'.repeat(101) } })
    fireEvent.click(screen.getByRole('button', { name: 'Save region' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('no more than 100 characters')
  })
})

describe('PropertyRegionField inside a list that stores the saved region', () => {
  it('keeps the "Region saved" message when the new region comes back through the props', async () => {
    setRegion.mockResolvedValue({ data: { id: 1, state: 'Bukhara' }, error: null })
    const { rerender } = render(<PropertyRegionField propertyId={1} region={null} />)

    fireEvent.change(screen.getByLabelText('Region'), { target: { value: 'Bukhara' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save region' }))
    await screen.findByRole('status')

    rerender(<PropertyRegionField propertyId={1} region="Bukhara" />)
    expect(screen.getByRole('status')).toHaveTextContent('Region saved')
  })
})
