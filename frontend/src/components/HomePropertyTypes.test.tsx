import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { HomePropertyTypes } from './HomePropertyTypes'
import { I18nProvider } from '../i18n/I18nContext'
import { propertyAdapter } from '../adapters/propertyAdapter'
import { settle } from '../test/utils'

vi.mock('../adapters/propertyAdapter', () => ({
  propertyAdapter: { getFilterOptions: vi.fn() },
}))

const options = vi.mocked(propertyAdapter.getFilterOptions)

function answer(types: Array<{ id: number; name: string; slug: string; count: number }>) {
  return { data: { property_types: types, features: [], amenities: [], price_range: { min: null, max: null }, sort_options: [] }, error: null }
}

function renderChips() {
  return render(
    <I18nProvider>
      <MemoryRouter>
        <HomePropertyTypes />
      </MemoryRouter>
    </I18nProvider>,
  )
}

describe('HomePropertyTypes', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('shows one link per property type with its real count, leading to the search page', async () => {
    options.mockResolvedValue(answer([
      { id: 9, name: 'Hotel', slug: 'hotel', count: 12 },
      { id: 7, name: 'Guesthouse', slug: 'guesthouse', count: 3 },
    ]) as never)
    renderChips()
    const nav = await screen.findByRole('navigation', { name: 'Property types' })
    const hotel = screen.getByRole('link', { name: /Hotel/ })
    expect(hotel).toHaveTextContent('Hotel')
    expect(hotel).toHaveTextContent('12')
    expect(hotel).toHaveAttribute('href', '/search?property_type=9')
    expect(screen.getByRole('link', { name: /Guesthouse/ })).toHaveAttribute('href', '/search?property_type=7')
    expect(nav.querySelectorAll('a')).toHaveLength(2)
  })

  it('does not show a type that has no hotels', async () => {
    options.mockResolvedValue(answer([
      { id: 9, name: 'Hotel', slug: 'hotel', count: 12 },
      { id: 5, name: 'Villa', slug: 'villa', count: 0 },
    ]) as never)
    renderChips()
    await screen.findByRole('link', { name: /Hotel/ })
    expect(screen.queryByRole('link', { name: /Villa/ })).toBeNull()
  })

  it('shows a skeleton while loading', () => {
    options.mockReturnValue(new Promise(() => {}))
    renderChips()
    expect(screen.getByRole('status', { name: 'Loading property types' })).toBeInTheDocument()
  })

  it('shows nothing when there are no types, on error and on a rejected request', async () => {
    options.mockResolvedValue(answer([]) as never)
    const empty = renderChips()
    await waitFor(() => expect(screen.queryByRole('status')).toBeNull())
    expect(empty.container).toBeEmptyDOMElement()
    empty.unmount()

    options.mockResolvedValue({ data: null, error: 'boom' } as never)
    const failed = renderChips()
    await waitFor(() => expect(screen.queryByRole('status')).toBeNull())
    expect(failed.container).toBeEmptyDOMElement()
    failed.unmount()

    options.mockRejectedValue(new Error('offline'))
    const rejected = renderChips()
    await waitFor(() => expect(screen.queryByRole('status')).toBeNull())
    expect(rejected.container).toBeEmptyDOMElement()
  })

  it('does not update after the page was left', async () => {
    let resolve: (value: ReturnType<typeof answer>) => void = () => {}
    options.mockReturnValue(new Promise(r => { resolve = r }) as never)
    const view = renderChips()
    view.unmount()
    resolve(answer([{ id: 9, name: 'Hotel', slug: 'hotel', count: 1 }]))
    await settle()
    expect(screen.queryByRole('link', { name: /Hotel/ })).toBeNull()
  })
})
