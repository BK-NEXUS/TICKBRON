import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import { AdminGeography } from './AdminGeography'
import { I18nProvider } from '../i18n/I18nContext'
import { adminGeographyAdapter } from '../adapters/adminGeographyAdapter'

vi.mock('../adapters/adminGeographyAdapter', () => ({
  adminGeographyAdapter: { list: vi.fn(), create: vi.fn(), update: vi.fn(), remove: vi.fn(), reorder: vi.fn() },
}))

const api = vi.mocked(adminGeographyAdapter)

const names = (en: string, uz: string, ru: string) => ({ name_en: en, name_uz: uz, name_ru: ru })
const COUNTRIES = [
  { id: 1, code: 'UZ', currency: 'UZS', ...names('Uzbekistan', 'Oʻzbekiston', 'Узбекистан'), is_active: true, sort_order: 0, region_count: 2, hotel_count: 5 },
  { id: 2, code: 'KZ', currency: 'KZT', ...names('Kazakhstan', 'Qozogʻiston', 'Казахстан'), is_active: false, sort_order: 1, region_count: 0, hotel_count: 0 },
]
const REGIONS = [
  { id: 10, country: 1, slug: 'tashkent', ...names('Tashkent', 'Toshkent', 'Ташкент'), is_active: true, sort_order: 0, city_count: 1, hotel_count: 3 },
  { id: 11, country: 1, slug: 'samarkand', ...names('Samarkand', 'Samarqand', 'Самарканд'), is_active: true, sort_order: 1, city_count: 0, hotel_count: 0 },
]
const CITIES = [
  { id: 100, region: 10, slug: 'chilanzar', ...names('Chilanzar', 'Chilonzor', 'Чиланзар'), is_active: true, sort_order: 0, hotel_count: 2 },
]
const page = <T,>(results: T[]) => ({ data: { count: results.length, next: null, previous: null, results }, error: null })

function renderScreen() {
  localStorage.setItem('tickbron.language', 'en')
  return render(<I18nProvider><AdminGeography /></I18nProvider>)
}

describe('AdminGeography', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.resetAllMocks()
    api.list.mockImplementation((async (kind: string) =>
      kind === 'countries' ? page(COUNTRIES) : kind === 'regions' ? page(REGIONS) : page(CITIES)) as never)
    api.update.mockResolvedValue({ data: {} as never, error: null })
    api.create.mockResolvedValue({ data: {} as never, error: null })
    api.reorder.mockResolvedValue({ data: {}, error: null })
    api.remove.mockResolvedValue({ error: null, inUse: false })
  })

  it('lists the countries with code, counts and status, hidden ones included', async () => {
    renderScreen()
    const row = (await screen.findByText('Uzbekistan')).closest('tr')!
    expect(within(row).getByText('UZ')).toBeInTheDocument()
    expect(within(row).getByText('Active')).toBeInTheDocument()
    expect(within(screen.getByText('Kazakhstan').closest('tr')!).getByText('Hidden')).toBeInTheDocument()
    expect(api.list).toHaveBeenCalledWith('countries', { search: '' })
  })

  it('opens a country to see its regions, then a region to see its cities, with a way back', async () => {
    renderScreen()
    fireEvent.click(await screen.findByRole('button', { name: 'Open Uzbekistan' }))
    expect(await screen.findByText('Tashkent')).toBeInTheDocument()
    expect(api.list).toHaveBeenLastCalledWith('regions', { search: '', country: 1 })

    fireEvent.click(screen.getByRole('button', { name: 'Open Tashkent' }))
    expect(await screen.findByText('Chilanzar')).toBeInTheDocument()
    expect(api.list).toHaveBeenLastCalledWith('cities', { search: '', region: 10 })
    expect(screen.queryByRole('button', { name: /^Open Chilanzar/ })).not.toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Uzbekistan' }))
    expect(await screen.findByText('Samarkand')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'All countries' }))
    expect(await screen.findByText('Kazakhstan')).toBeInTheDocument()
  })

  it('searches the current list', async () => {
    renderScreen()
    await screen.findByText('Uzbekistan')
    fireEvent.change(screen.getByLabelText('Search by name'), { target: { value: 'kaz' } })
    await waitFor(() => expect(api.list).toHaveBeenLastCalledWith('countries', { search: 'kaz' }))
  })

  it('adds a country with code, currency and three names', async () => {
    renderScreen()
    await screen.findByText('Uzbekistan')
    fireEvent.click(screen.getByRole('button', { name: 'New country' }))
    const dialog = screen.getByRole('dialog')
    fireEvent.change(within(dialog).getByLabelText('Code (2 letters)'), { target: { value: 'tr' } })
    fireEvent.change(within(dialog).getByLabelText('Currency (3 letters)'), { target: { value: 'try' } })
    fireEvent.change(within(dialog).getByLabelText('Name (Uzbek)'), { target: { value: 'Turkiya' } })
    fireEvent.change(within(dialog).getByLabelText('Name (Russian)'), { target: { value: 'Турция' } })
    fireEvent.change(within(dialog).getByLabelText('Name (English)'), { target: { value: 'Turkey' } })
    fireEvent.click(within(dialog).getByRole('button', { name: 'Save' }))

    await waitFor(() => expect(api.create).toHaveBeenCalledWith('countries', {
      code: 'tr', currency: 'try', name_uz: 'Turkiya', name_ru: 'Турция', name_en: 'Turkey',
    }))
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
    expect(api.list.mock.calls.filter(([kind]) => kind === 'countries').length).toBeGreaterThan(1)
  })

  it('a new region belongs to the open country', async () => {
    renderScreen()
    fireEvent.click(await screen.findByRole('button', { name: 'Open Uzbekistan' }))
    await screen.findByText('Tashkent')
    fireEvent.click(screen.getByRole('button', { name: 'New region' }))
    const dialog = screen.getByRole('dialog')
    fireEvent.change(within(dialog).getByLabelText('Name (Uzbek)'), { target: { value: 'Buxoro' } })
    fireEvent.change(within(dialog).getByLabelText('Name (Russian)'), { target: { value: 'Бухара' } })
    fireEvent.change(within(dialog).getByLabelText('Name (English)'), { target: { value: 'Bukhara' } })
    fireEvent.click(within(dialog).getByRole('button', { name: 'Save' }))
    await waitFor(() => expect(api.create).toHaveBeenCalledWith('regions', {
      country: 1, name_uz: 'Buxoro', name_ru: 'Бухара', name_en: 'Bukhara',
    }))
  })

  it('shows the server error in the form and keeps it open', async () => {
    api.create.mockResolvedValue({ data: null, error: 'A region with this name already exists.' })
    renderScreen()
    fireEvent.click(await screen.findByRole('button', { name: 'Open Uzbekistan' }))
    await screen.findByText('Tashkent')
    fireEvent.click(screen.getByRole('button', { name: 'New region' }))
    const dialog = screen.getByRole('dialog')
    for (const label of ['Name (Uzbek)', 'Name (Russian)', 'Name (English)']) {
      fireEvent.change(within(dialog).getByLabelText(label), { target: { value: 'Tashkent' } })
    }
    fireEvent.click(within(dialog).getByRole('button', { name: 'Save' }))
    expect(await within(dialog).findByRole('alert')).toHaveTextContent('already exists')
  })

  it('edits the names of a row (the code stays)', async () => {
    renderScreen()
    fireEvent.click(await screen.findByRole('button', { name: 'Edit Uzbekistan' }))
    const dialog = screen.getByRole('dialog')
    expect(within(dialog).getByLabelText('Name (English)')).toHaveValue('Uzbekistan')
    expect(within(dialog).queryByLabelText('Code (2 letters)')).not.toBeInTheDocument()
    fireEvent.change(within(dialog).getByLabelText('Name (English)'), { target: { value: 'Republic of Uzbekistan' } })
    fireEvent.click(within(dialog).getByRole('button', { name: 'Save' }))
    await waitFor(() => expect(api.update).toHaveBeenCalledWith('countries', 1, {
      name_uz: 'Oʻzbekiston', name_ru: 'Узбекистан', name_en: 'Republic of Uzbekistan',
    }))
  })

  it('hides and shows a row', async () => {
    renderScreen()
    fireEvent.click(await screen.findByRole('button', { name: 'Hide Uzbekistan' }))
    await waitFor(() => expect(api.update).toHaveBeenCalledWith('countries', 1, { is_active: false }))
    fireEvent.click(screen.getByRole('button', { name: 'Show Kazakhstan' }))
    await waitFor(() => expect(api.update).toHaveBeenCalledWith('countries', 2, { is_active: true }))
  })

  it('moves a row up or down by sending the whole new order', async () => {
    renderScreen()
    fireEvent.click(await screen.findByRole('button', { name: 'Move Uzbekistan down' }))
    await waitFor(() => expect(api.reorder).toHaveBeenCalledWith('countries', [2, 1]))
  })

  it('the first row cannot move up and the last cannot move down', async () => {
    renderScreen()
    expect(await screen.findByRole('button', { name: 'Move Uzbekistan up' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Move Kazakhstan down' })).toBeDisabled()
  })

  it('does not reorder while a search is active', async () => {
    renderScreen()
    await screen.findByText('Uzbekistan')
    fireEvent.change(screen.getByLabelText('Search by name'), { target: { value: 'u' } })
    await waitFor(() => expect(api.list).toHaveBeenLastCalledWith('countries', { search: 'u' }))
    expect(screen.getByRole('button', { name: 'Move Uzbekistan down' })).toBeDisabled()
  })

  it('deletes after a confirmation', async () => {
    renderScreen()
    fireEvent.click(await screen.findByRole('button', { name: 'Delete Kazakhstan' }))
    const dialog = screen.getByRole('dialog')
    expect(dialog).toHaveTextContent('Delete Kazakhstan? This cannot be undone.')
    fireEvent.click(within(dialog).getByRole('button', { name: 'Delete' }))
    await waitFor(() => expect(api.remove).toHaveBeenCalledWith('countries', 2))
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
  })

  it('a row in use cannot be deleted: the screen says to hide it', async () => {
    api.remove.mockResolvedValue({ error: 'Conflict', inUse: true })
    renderScreen()
    fireEvent.click(await screen.findByRole('button', { name: 'Delete Uzbekistan' }))
    fireEvent.click(within(screen.getByRole('dialog')).getByRole('button', { name: 'Delete' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Hide it instead')
  })

  it('shows loading, an error with retry, and the empty state', async () => {
    api.list.mockResolvedValueOnce({ data: null, error: 'boom' })
    renderScreen()
    expect(screen.getByText('Loading...')).toBeInTheDocument()
    expect(await screen.findByRole('alert')).toHaveTextContent('Could not load the list.')
    api.list.mockResolvedValueOnce(page([]))
    fireEvent.click(screen.getByRole('button', { name: 'Try Again' }))
    expect(await screen.findByText('Nothing here yet.')).toBeInTheDocument()
  })
})
