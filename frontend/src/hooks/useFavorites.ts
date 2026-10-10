import { useCallback, useEffect, useSyncExternalStore } from 'react'
import { accountAdapter } from '../adapters/accountAdapter'
import { useAuth } from '../contexts/AuthContext'

/**
 * Favorites of the logged-in user, shared by every heart button on the page.
 * The list is loaded once per user; add/remove keep it in sync.
 */
let favoriteIdByProperty = new Map<number, number>()
let loadedForUser: number | null = null
let loading: Promise<void> | null = null
let version = 0
const listeners = new Set<() => void>()

function notify() {
  version += 1
  listeners.forEach((listener) => listener())
}

function subscribe(listener: () => void) {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

async function loadFavorites(userId: number) {
  const response = await accountAdapter.getFavorites()
  if (loadedForUser !== userId) return
  favoriteIdByProperty = new Map((response.data ?? []).map((favorite) => [favorite.property, favorite.id]))
  notify()
}

function ensureLoaded(userId: number) {
  if (loadedForUser === userId && loading) return loading
  loadedForUser = userId
  favoriteIdByProperty = new Map()
  loading = loadFavorites(userId)
  return loading
}

/** Forget everything (logout, tests). */
export function resetFavoritesStore() {
  favoriteIdByProperty = new Map()
  loadedForUser = null
  loading = null
  notify()
}

/** Keep heart buttons in sync when a favorite is removed elsewhere (e.g. the favorites page). */
export function markFavoriteRemoved(propertyId: number) {
  if (favoriteIdByProperty.delete(propertyId)) notify()
}

/** useAuth that also works outside an AuthProvider (treated as logged out). */
function useAuthIfAvailable() {
  try {
    return useAuth()
  } catch {
    return null
  }
}

export function useFavorites() {
  const auth = useAuthIfAvailable()
  const userId = auth?.isAuthenticated && auth.user ? auth.user.id : null
  useSyncExternalStore(subscribe, () => version)

  useEffect(() => {
    if (userId !== null) {
      ensureLoaded(userId)
    } else if (loadedForUser !== null) {
      resetFavoritesStore()
    }
  }, [userId])

  const toggle = useCallback(async (propertyId: number): Promise<boolean> => {
    if (userId === null) return false
    const favoriteId = favoriteIdByProperty.get(propertyId)
    if (favoriteId !== undefined) {
      const response = await accountAdapter.removeFavorite(favoriteId)
      if (response.error) return false
      markFavoriteRemoved(propertyId)
      return true
    }
    const response = await accountAdapter.addFavorite(propertyId)
    // The create response has no id; reload the list to learn it (also covers "already saved")
    loading = loadFavorites(userId)
    await loading
    return !response.error
  }, [userId])

  return {
    isAuthenticated: userId !== null,
    /** True while the session is still being checked: the visitor may be logged in already */
    sessionLoading: Boolean(auth?.isLoading),
    isFavorite: (propertyId: number) => favoriteIdByProperty.has(propertyId),
    toggle,
  }
}
