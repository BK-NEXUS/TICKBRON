import { NearbyPlace } from '../adapters/propertyAdapter'

interface NearbyPlacesProps {
  places?: NearbyPlace[]
}

/**
 * NearbyPlaces component for displaying nearby attractions and places
 * Shows distance, rating, and category information
 */
export function NearbyPlaces({ places = [] }: NearbyPlacesProps) {
  if (places.length === 0) {
    return (
      <div className="nearby-places nearby-places--empty">
        <p className="nearby-places-empty">No nearby places information available</p>
      </div>
    )
  }

  // Sort by distance
  const sortedPlaces = [...places].sort((a, b) => a.distance - b.distance)

  return (
    <div className="nearby-places">
      <h2 className="nearby-places-title">What's Nearby</h2>
      
      <div className="nearby-places-list">
        {sortedPlaces.map((place) => (
          <div key={place.id} className="nearby-place-item" data-testid={`nearby-place-item-${place.id}`}>
            <div className="nearby-place-item-header">
              <h3 className="nearby-place-item-name">{place.name}</h3>
              <div className="nearby-place-item-meta">
                <span className="nearby-place-item-category">{place.category}</span>
                <span className="nearby-place-item-distance">
                  {place.distance} {place.distance_unit}
                </span>
              </div>
            </div>
            
            {place.rating && (
              <div className="nearby-place-item-rating">
                <span className="nearby-place-item-rating-value">★ {place.rating.toFixed(1)}</span>
              </div>
            )}
            
            {place.address && (
              <p className="nearby-place-item-address">{place.address}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}