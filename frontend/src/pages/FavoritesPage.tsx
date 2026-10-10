import { useI18n } from '../i18n/I18nContext'
import { useState, useEffect } from 'react'
import { Lock, Heart, House } from 'lucide-react'
import { Link } from 'react-router-dom'
import { accountAdapter, Favorite } from '../adapters/accountAdapter'
import { EmptyState } from '../components/EmptyState'
import { useAuth } from '../contexts/AuthContext'
import { markFavoriteRemoved } from '../hooks/useFavorites'

/** Display name of a favorite: its first translation, else the city */
const favoriteName = (favorite: Favorite) => favorite.property_translations?.[0]?.name || favorite.property_city

export function FavoritesPage() {
  const { t, tp, formatMoney } = useI18n()
  const { isAuthenticated, isLoading: sessionLoading } = useAuth()
  const [favorites, setFavorites] = useState<Favorite[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!isAuthenticated) {
      setLoading(false)
      return
    }

    const loadFavorites = async () => {
      setLoading(true)
      setError(null)
      const result = await accountAdapter.getFavorites()
      
      if (result.error) {
        setError(result.error)
      } else {
        setFavorites(result.data || [])
      }
      setLoading(false)
    }

    loadFavorites()
  }, [isAuthenticated])

  const handleRemoveFavorite = async (favoriteId: number) => {
    const result = await accountAdapter.removeFavorite(favoriteId)
    
    if (result.error) {
      setError(result.error)
    } else {
      const removed = favorites.find(fav => fav.id === favoriteId)
      if (removed) markFavoriteRemoved(removed.property)
      setFavorites(favorites.filter(fav => fav.id !== favoriteId))
    }
  }

  if (!isAuthenticated && !sessionLoading) {
    return (
      <div className="favorites-page">
        <div className="container">
          <EmptyState
            icon={<Lock size={40} />}
            title={t('common.signInRequired')}
            message={t('favorites.signInText')}
            ctaText={t('auth.signIn')}
            ctaLink="/login"
          />
        </div>
      </div>
    )
  }

  if (loading || sessionLoading) {
    return (
      <div className="favorites-page">
        <div className="container">
          <div className="loading-state">
            <div className="spinner" role="status" aria-live="polite">
              <span className="sr-only">{t('common.loading')}</span>
            </div>
            <p>{t('favorites.loading')}</p>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="favorites-page">
        <div className="container">
          <div className="error-state" role="alert" aria-live="assertive">
            <p>{error}</p>
            <button 
              onClick={() => window.location.reload()}
              className="btn btn-primary"
            >
              {t('common.tryAgain')}
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (favorites.length === 0) {
    return (
      <div className="favorites-page">
        <div className="container">
          <EmptyState
            icon={<Heart size={40} />}
            title={t('favorites.emptyTitle')}
            message={t('favorites.emptyText')}
            ctaText={t('favorites.emptyCta')}
            ctaLink="/search"
          />
        </div>
      </div>
    )
  }

  return (
    <div className="favorites-page">
      <div className="container">
        <h1 className="favorites-page-title">{t('favorites.title')}</h1>
        <p className="favorites-page-count">{tp('favorites.count', favorites.length)}</p>
        
        <div className="favorites-grid">
          {favorites.map((favorite) => (
            <div key={favorite.id} className="favorite-card">
              <div className="favorite-card-image">
                {favorite.property_primary_photo ? (
                  <img 
                    src={favorite.property_primary_photo} 
                    alt={favoriteName(favorite)}
                    loading="lazy"
                  />
                ) : (
                  <div className="favorite-card-placeholder"><House size={40} /></div>
                )}
              </div>
              
              <div className="favorite-card-content">
                <h3 className="favorite-card-title">
                  <Link to={`/property/${favorite.property}`}>
                    {favoriteName(favorite)}
                  </Link>
                </h3>
                
                <p className="favorite-card-location">
                  {favorite.property_city}, {favorite.property_country}
                </p>
                
                <p className="favorite-card-price">
                  {t('favorites.perNight', { price: formatMoney(favorite.property_base_price, favorite.property_currency, { minDecimals: 0, maxDecimals: 2 }) })}
                </p>
                
                {favorite.notes && (
                  <p className="favorite-card-notes">{favorite.notes}</p>
                )}
              </div>
              
              <div className="favorite-card-actions">
                <button
                  onClick={() => handleRemoveFavorite(favorite.id)}
                  className="btn btn-danger"
                  aria-label={t('fav.remove', { name: favoriteName(favorite) })}
                >
                  {t('favorites.remove')}
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default FavoritesPage
