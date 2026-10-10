import { useI18n } from '../i18n/I18nContext'
import { useState } from 'react'
import { Heart } from 'lucide-react'
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
  const { t } = useI18n()
  const navigate = useNavigate()
  // While the session is being checked a logged-in guest still looks logged out: do not send them to the login page
  const { isAuthenticated, sessionLoading, isFavorite, toggle } = useFavorites()
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
      disabled={saving || sessionLoading}
      aria-busy={saving || sessionLoading}
      aria-pressed={saved}
      aria-label={saved ? t('fav.remove', { name: propertyName }) : t('fav.save', { name: propertyName })}
      title={saved ? t('fav.removeTitle') : t('fav.saveTitle')}
    >
      <Heart size={18} aria-hidden="true" fill={saved ? 'currentColor' : 'none'} />
      {variant === 'detail' && <span className="favorite-button-label">{saved ? 'Saved' : 'Save'}</span>}
    </button>
  )
}
