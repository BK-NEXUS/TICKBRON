import { EmptyState } from '../components/EmptyState'

export function FavoritesPage() {
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
