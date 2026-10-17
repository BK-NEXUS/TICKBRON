import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { StatusCsvButton } from './StatusCsvButton'
import { saveBlob } from '../utils/saveBlob'

vi.mock('../utils/saveBlob', () => ({ saveBlob: vi.fn() }))

const file = { blob: new Blob(['x']), filename: 'status_hotels.csv' }

describe('StatusCsvButton', () => {
  beforeEach(() => vi.mocked(saveBlob).mockReset())

  it('exports and saves the file', async () => {
    const onExport = vi.fn().mockResolvedValue({ data: file, error: null })
    render(<StatusCsvButton onExport={onExport} />)

    fireEvent.click(screen.getByRole('button', { name: 'Export CSV' }))

    await waitFor(() => expect(saveBlob).toHaveBeenCalledWith(file.blob, 'status_hotels.csv'))
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('is disabled and says so while exporting', async () => {
    let finish: (value: unknown) => void = () => {}
    const onExport = vi.fn(() => new Promise(resolve => { finish = resolve }))
    render(<StatusCsvButton onExport={onExport as never} />)

    fireEvent.click(screen.getByRole('button', { name: 'Export CSV' }))

    const busy = await screen.findByRole('button', { name: 'Exporting...' })
    expect(busy).toBeDisabled()
    finish({ data: file, error: null })
    expect(await screen.findByRole('button', { name: 'Export CSV' })).toBeEnabled()
  })

  it('shows the error and saves nothing', async () => {
    const onExport = vi.fn().mockResolvedValue({ data: null, error: 'Admin or staff role required' })
    render(<StatusCsvButton onExport={onExport} />)

    fireEvent.click(screen.getByRole('button', { name: 'Export CSV' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Admin or staff role required')
    expect(saveBlob).not.toHaveBeenCalled()
  })

  it('asks for the file type of the button that was clicked', async () => {
    const onExport = vi.fn().mockResolvedValue({ data: file, error: null })
    render(<StatusCsvButton onExport={onExport} />)

    fireEvent.click(screen.getByRole('button', { name: 'Export CSV' }))
    await waitFor(() => expect(onExport).toHaveBeenLastCalledWith('csv'))
    fireEvent.click(screen.getByRole('button', { name: 'Export Excel' }))
    await waitFor(() => expect(onExport).toHaveBeenLastCalledWith('xlsx'))
    expect(saveBlob).toHaveBeenCalledTimes(2)
  })

  it('disables both buttons while one export runs', async () => {
    let finish: (value: unknown) => void = () => {}
    render(<StatusCsvButton onExport={(() => new Promise(resolve => { finish = resolve })) as never} />)

    fireEvent.click(screen.getByRole('button', { name: 'Export Excel' }))

    expect(await screen.findByRole('button', { name: 'Export CSV' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Exporting...' })).toBeDisabled()
    finish({ data: file, error: null })
    expect(await screen.findByRole('button', { name: 'Export Excel' })).toBeEnabled()
  })
})
