/**
 * E2E BUG 4: there was no way to add a property to favorites.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { FavoriteButton } from './FavoriteButton'
import { accountAdapter } from '../adapters/accountAdapter'
import { resetFavoritesStore } from '../hooks/useFavorites'

const mockNavigate = vi.fn()
vi.mock('react-router-dom', () => ({ useNavigate: () => mockNavigate }))

const auth = { isAuthenticated: false, user: null as { id: number } | null }
vi.mock('../contexts/AuthContext', () => ({ useAuth: () => auth }))

vi.mock('../adapters/accountAdapter', () => ({
  accountAdapter: { getFavorites: vi.fn(), addFavorite: vi.fn(), removeFavorite: vi.fn() },
}))

const favorite = (id: number, property: number) => ({ id, property } as never)

describe('FavoriteButton', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    resetFavoritesStore()
    auth.isAuthenticated = false
    auth.user = null
  })

  it('sends visitors who are not logged in to the login page', () => {
    render(<FavoriteButton propertyId={5} propertyName="Hotel Tashkent" />)

    fireEvent.click(screen.getByRole('button', { name: 'Save Hotel Tashkent to favorites' }))

    expect(mockNavigate).toHaveBeenCalledWith('/login', expect.objectContaining({ state: expect.anything() }))
    expect(accountAdapter.addFavorite).not.toHaveBeenCalled()
  })

  it('adds the property for a logged-in user', async () => {
    auth.isAuthenticated = true
    auth.user = { id: 3 }
    vi.mocked(accountAdapter.getFavorites)
      .mockResolvedValueOnce({ data: [], error: null })
      .mockResolvedValueOnce({ data: [favorite(9, 5)], error: null })
    vi.mocked(accountAdapter.addFavorite).mockResolvedValue({ data: null, error: null })
    render(<FavoriteButton propertyId={5} propertyName="Hotel Tashkent" />)

    const button = await screen.findByRole('button', { name: 'Save Hotel Tashkent to favorites' })
    expect(button).toHaveAttribute('aria-pressed', 'false')
    fireEvent.click(button)

    expect(accountAdapter.addFavorite).toHaveBeenCalledWith(5)
    const saved = await screen.findByRole('button', { name: 'Remove Hotel Tashkent from favorites' })
    expect(saved).toHaveAttribute('aria-pressed', 'true')
  })

  it('removes a property that is already a favorite', async () => {
    auth.isAuthenticated = true
    auth.user = { id: 3 }
    vi.mocked(accountAdapter.getFavorites).mockResolvedValue({ data: [favorite(9, 5)], error: null })
    vi.mocked(accountAdapter.removeFavorite).mockResolvedValue({ data: null, error: null })
    render(<FavoriteButton propertyId={5} propertyName="Hotel Tashkent" />)

    fireEvent.click(await screen.findByRole('button', { name: 'Remove Hotel Tashkent from favorites' }))

    expect(accountAdapter.removeFavorite).toHaveBeenCalledWith(9)
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Save Hotel Tashkent to favorites' })).toHaveAttribute('aria-pressed', 'false')
    })
  })

  it('loads the favorites list once for many buttons', async () => {
    auth.isAuthenticated = true
    auth.user = { id: 3 }
    vi.mocked(accountAdapter.getFavorites).mockResolvedValue({ data: [favorite(9, 5)], error: null })
    render(
      <>
        <FavoriteButton propertyId={5} propertyName="A" />
        <FavoriteButton propertyId={6} propertyName="B" />
        <FavoriteButton propertyId={7} propertyName="C" />
      </>
    )

    expect(await screen.findByRole('button', { name: 'Remove A from favorites' })).toBeInTheDocument()
    expect(accountAdapter.getFavorites).toHaveBeenCalledTimes(1)
  })
})
