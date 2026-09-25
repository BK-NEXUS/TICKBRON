import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useFavorites } from '../hooks/useFavorites'

interface FavoriteButtonProps {
  propertyId: number
  propertyName: string
  /** 'card' sits on a property card, 'detail' next to the property page title */
  variant?: 'card' | 'detail'
}

/** Heart toggle: saves / removes a property; sends visitors who are not logged in to the login page. */
export function FavoriteButton({ propertyId, propertyName, variant = 'card' }: FavoriteButtonProps) {
  const navigate = useNavigate()
  const { isAuthenticated, isFavorite, toggle } = useFavorites()
  const [saving, setSaving] = useState(false)
  const saved = isFavorite(propertyId)

  const handleClick = async (event: React.MouseEvent) => {
    // Cards are clickable as a whole; the heart must not open the property
    event.stopPropagation()
    event.preventDefault()
    if (!isAuthenticated) {
      navigate('/login', { state: { from: { pathname: window.location.pathname } } })
      return
    }
    setSaving(true)
    await toggle(propertyId)
    setSaving(false)
  }

  return (
    <button
      type="button"
      className={`favorite-button favorite-button--${variant} ${saved ? 'favorite-button--saved' : ''}`}
      onClick={handleClick}
      onKeyDown={(event) => event.stopPropagation()}
      disabled={saving}
      aria-pressed={saved}
      aria-label={saved ? `Remove ${propertyName} from favorites` : `Save ${propertyName} to favorites`}
      title={saved ? 'Remove from favorites' : 'Save to favorites'}
    >
      <span aria-hidden="true">{saved ? '♥' : '♡'}</span>
      {variant === 'detail' && <span className="favorite-button-label">{saved ? 'Saved' : 'Save'}</span>}
    </button>
  )
}
