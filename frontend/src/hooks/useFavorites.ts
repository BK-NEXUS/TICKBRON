import { useCallback, useEffect, useSyncExternalStore } from 'react'
import { accountAdapter } from '../adapters/accountAdapter'
import { useAuth } from '../contexts/AuthContext'

/**
 * Kirgen paydalanıwshınıń favorit leri, bettegi hár júrek túymesi ortaq paydalanadı.
 * Dizim hár paydalanıwshı ushın bir márte júklenedi; qosıw/alıp taslaw onı sinxron saqlaydı.
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

/** Hámmesin umıtıw (shıǵıw, testler). */
export function resetFavoritesStore() {
  favoriteIdByProperty = new Map()
  loadedForUser = null
  loading = null
  notify()
}

/** Favorit basqa jerde (mısalı favorit ler betinde) alıp taslanǵanda júrek túymelerin sinxron saqlaw. */
export function markFavoriteRemoved(propertyId: number) {
  if (favoriteIdByProperty.delete(propertyId)) notify()
}

/** AuthProvider sırtında da isleytuǵın useAuth (kirmegen dep esaplanadı). */
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
    // Jaratıw juwabında id joq; onı biliw ushın dizimdi qayta júkleń ("aldınan saqlanǵan" jaǵdayın da qaplaydı)
    loading = loadFavorites(userId)
    await loading
    return !response.error
  }, [userId])

  return {
    isAuthenticated: userId !== null,
    /** Session ele tekserilip atırǵanda true: kelwshi aldınan kirgen bolıwı múmkin */
    sessionLoading: Boolean(auth?.isLoading),
    isFavorite: (propertyId: number) => favoriteIdByProperty.has(propertyId),
    toggle,
  }
}
