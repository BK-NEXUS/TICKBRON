/**
 * A new country or region needs a picture; an edit keeps the old one unless a new one is chosen.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import { GeographyRowDialog } from './GeographyRowDialog'
import { I18nProvider } from '../i18n/I18nContext'
import { adminGeographyAdapter } from '../adapters/adminGeographyAdapter'

vi.mock('../adapters/adminGeographyAdapter', () => ({
  adminGeographyAdapter: { create: vi.fn(), update: vi.fn() },
}))
const api = vi.mocked(adminGeographyAdapter)

const png = (name = 'flag.png') => new File(['x'], name, { type: 'image/png' })
const names = { name_uz: 'Turkiya', name_ru: 'Турция', name_en: 'Turkey' }

function renderDialog(props: Partial<React.ComponentProps<typeof GeographyRowDialog>> = {}) {
  localStorage.setItem('tickbron.language', 'en')
  const onSaved = vi.fn()
  render(<I18nProvider><GeographyRowDialog kind="countries" parentId={null} onSaved={onSaved} onClose={() => {}} {...props} /></I18nProvider>)
  return { onSaved }
}

function fillNames() {
  const dialog = screen.getByRole('dialog')
  fireEvent.change(within(dialog).getByLabelText('Name (Uzbek)'), { target: { value: names.name_uz } })
  fireEvent.change(within(dialog).getByLabelText('Name (Russian)'), { target: { value: names.name_ru } })
  fireEvent.change(within(dialog).getByLabelText('Name (English)'), { target: { value: names.name_en } })
}

describe('GeographyRowDialog picture', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.resetAllMocks()
    api.create.mockResolvedValue({ data: {} as never, error: null })
    api.update.mockResolvedValue({ data: {} as never, error: null })
    vi.stubGlobal('URL', Object.assign(URL, { createObjectURL: vi.fn(() => 'blob:preview'), revokeObjectURL: vi.fn() }))
  })
  afterEach(() => vi.unstubAllGlobals())

  it('refuses to add a country without a picture and says so', async () => {
    renderDialog()
    const dialog = screen.getByRole('dialog')
    fireEvent.change(within(dialog).getByLabelText('Code (2 letters)'), { target: { value: 'tr' } })
    fireEvent.change(within(dialog).getByLabelText('Currency (3 letters)'), { target: { value: 'try' } })
    fillNames()
    fireEvent.click(within(dialog).getByRole('button', { name: 'Save' }))
    expect(await within(dialog).findByRole('alert')).toHaveTextContent('Choose a picture.')
    expect(api.create).not.toHaveBeenCalled()
  })

  it('sends the chosen picture with a new country and shows a preview', async () => {
    const { onSaved } = renderDialog()
    const dialog = screen.getByRole('dialog')
    fireEvent.change(within(dialog).getByLabelText('Code (2 letters)'), { target: { value: 'tr' } })
    fireEvent.change(within(dialog).getByLabelText('Currency (3 letters)'), { target: { value: 'try' } })
    fillNames()
    const file = png()
    fireEvent.change(within(dialog).getByLabelText('Picture'), { target: { files: [file] } })
    expect(within(dialog).getByRole('img', { name: 'Preview' })).toHaveAttribute('src', 'blob:preview')
    fireEvent.click(within(dialog).getByRole('button', { name: 'Save' }))
    await waitFor(() => expect(api.create).toHaveBeenCalledWith('countries', { code: 'tr', currency: 'try', ...names, image: file }))
    await waitFor(() => expect(onSaved).toHaveBeenCalled())
  })

  it('rejects a file of the wrong type or size before it is sent', () => {
    renderDialog({ kind: 'regions', parentId: 1 })
    const dialog = screen.getByRole('dialog')
    fireEvent.change(within(dialog).getByLabelText('Picture'), { target: { files: [new File(['x'], 'a.bmp', { type: 'image/bmp' })] } })
    expect(within(dialog).getByRole('alert')).toHaveTextContent('Use a JPG, PNG, WebP or GIF picture.')
    fireEvent.change(within(dialog).getByLabelText('Picture'), { target: { files: [new File([new Uint8Array(10 * 1024 * 1024 + 1)], 'big.png', { type: 'image/png' })] } })
    expect(within(dialog).getByRole('alert')).toHaveTextContent('The picture is larger than 10 MB.')
    expect(within(dialog).queryByRole('img', { name: 'Preview' })).not.toBeInTheDocument()
  })

  it('a new region needs a picture too', async () => {
    renderDialog({ kind: 'regions', parentId: 1 })
    fillNames()
    fireEvent.click(within(screen.getByRole('dialog')).getByRole('button', { name: 'Save' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Choose a picture.')
    expect(api.create).not.toHaveBeenCalled()
  })

  it('cities have no picture field', () => {
    renderDialog({ kind: 'cities', parentId: 10 })
    expect(screen.queryByLabelText('Picture')).not.toBeInTheDocument()
  })

  const row = { id: 3, ...names, is_active: true, sort_order: 0, hotel_count: 0, code: 'TR', currency: 'TRY', region_count: 0, image_url: '/media/geography/countries/a.png' }

  it('editing shows the current picture and sends no image when none is chosen', async () => {
    renderDialog({ row })
    const dialog = screen.getByRole('dialog')
    expect(within(dialog).getByRole('img', { name: 'Preview' })).toHaveAttribute('src', expect.stringContaining('/media/geography/countries/a.png'))
    fireEvent.click(within(dialog).getByRole('button', { name: 'Save' }))
    await waitFor(() => expect(api.update).toHaveBeenCalledWith('countries', 3, names))
  })

  it('editing with a new picture sends it', async () => {
    renderDialog({ row })
    const dialog = screen.getByRole('dialog')
    const file = png('new.png')
    fireEvent.change(within(dialog).getByLabelText('Picture'), { target: { files: [file] } })
    fireEvent.click(within(dialog).getByRole('button', { name: 'Save' }))
    await waitFor(() => expect(api.update).toHaveBeenCalledWith('countries', 3, { ...names, image: file }))
  })
})
