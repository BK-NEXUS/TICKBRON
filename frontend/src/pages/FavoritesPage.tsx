import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { accountAdapter, Favorite } from '../adapters/accountAdapter'
import { EmptyState } from '../components/EmptyState'
import { useAuth } from '../contexts/AuthContext'

export function FavoritesPage() {
  const { isAuthenticated } = useAuth()
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
      setFavorites(favorites.filter(fav => fav.id !== favoriteId))
    }
  }

  if (!isAuthenticated) {
    return (
      <div className="favorites-page">
        <div className="container">
          <EmptyState
            icon="🔒"
            title="Sign in required"
            message="Please sign in to view your favorite properties."
            ctaText="Sign In"
            ctaLink="/login"
          />
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="favorites-page">
        <div className="container">
          <div className="loading-state">
            <div className="spinner" role="status" aria-live="polite">
              <span className="sr-only">Loading...</span>
            </div>
            <p>Loading favorites...</p>
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
              Try Again
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
            icon="❤️"
            title="No favorites yet"
            message="Save your favorite properties to view them here."
            ctaText="Explore Properties"
            ctaLink="/search"
          />
        </div>
      </div>
    )
  }

  return (
    <div className="favorites-page">
      <div className="container">
        <h1 className="favorites-page-title">My Favorites</h1>
        <p className="favorites-page-count">{favorites.length} properties saved</p>
        
        <div className="favorites-grid">
          {favorites.map((favorite) => (
            <div key={favorite.id} className="favorite-card">
              <div className="favorite-card-image">
                {favorite.primary_photo ? (
                  <img 
                    src={favorite.primary_photo} 
                    alt={favorite.property_name}
                    loading="lazy"
                  />
                ) : (
                  <div className="favorite-card-placeholder">🏠</div>
                )}
              </div>
              
              <div className="favorite-card-content">
                <h3 className="favorite-card-title">
                  <Link to={`/property/${favorite.property}`}>
                    {favorite.property_name}
                  </Link>
                </h3>
                
                <p className="favorite-card-location">
                  {favorite.city}, {favorite.country}
                </p>
                
                <p className="favorite-card-price">
                  ${favorite.base_price} {favorite.currency} / night
                </p>
                
                {favorite.notes && (
                  <p className="favorite-card-notes">{favorite.notes}</p>
                )}
              </div>
              
              <div className="favorite-card-actions">
                <button
                  onClick={() => handleRemoveFavorite(favorite.id)}
                  className="btn btn-danger"
                  aria-label={`Remove ${favorite.property_name} from favorites`}
                >
                  Remove
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
