import { Restaurant } from '../adapters/searchAdapter'

interface DiningRestaurantsProps {
  restaurants?: Restaurant[]
}

/**
 * DiningRestaurants component for displaying nearby restaurants and dining options
 * Shows cuisine, distance, rating, and price range information
 */
export function DiningRestaurants({ restaurants = [] }: DiningRestaurantsProps) {
  if (restaurants.length === 0) {
    return (
      <div className="dining-restaurants dining-restaurants--empty">
        <p className="dining-restaurants-empty">No restaurant information available</p>
      </div>
    )
  }

  // Sort by distance
  const sortedRestaurants = [...restaurants].sort((a, b) => a.distance - b.distance)

  const formatPriceRange = (priceRange: string) => {
    switch (priceRange) {
      case '$':
        return 'Budget-friendly'
      case '$$':
        return 'Moderate'
      case '$$$':
        return 'Expensive'
      case '$$$$':
        return 'Fine dining'
      default:
        return priceRange
    }
  }

  return (
    <div className="dining-restaurants">
      <h2 className="dining-restaurants-title">Dining & Restaurants</h2>
      
      <div className="dining-restaurants-list">
        {sortedRestaurants.map((restaurant) => (
          <div key={restaurant.id} className="dining-restaurant-item" data-testid={`dining-restaurant-item-${restaurant.id}`}>
            <div className="dining-restaurant-item-header">
              <h3 className="dining-restaurant-item-name">{restaurant.name}</h3>
              <div className="dining-restaurant-item-meta">
                <span className="dining-restaurant-item-cuisine">{restaurant.cuisine}</span>
                <span className="dining-restaurant-item-distance">
                  {restaurant.distance} {restaurant.distance_unit}
                </span>
              </div>
            </div>
            
            <div className="dining-restaurant-item-details">
              {restaurant.rating && (
                <div className="dining-restaurant-item-rating">
                  <span className="dining-restaurant-item-rating-value">★ {restaurant.rating.toFixed(1)}</span>
                </div>
              )}
              
              <div className="dining-restaurant-item-price">
                <span className="dining-restaurant-item-price-range">
                  {restaurant.price_range}
                </span>
                <span className="dining-restaurant-item-price-label">
                  {formatPriceRange(restaurant.price_range)}
                </span>
              </div>
            </div>
            
            {restaurant.address && (
              <p className="dining-restaurant-item-address">{restaurant.address}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}