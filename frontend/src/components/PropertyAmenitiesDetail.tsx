import { PropertyAmenity, AmenityCategory } from '../adapters/propertyAdapter'

interface PropertyAmenitiesDetailProps {
  amenities?: PropertyAmenity[]
}

/**
 * PropertyAmenitiesDetail component for displaying detailed property amenities
 * Groups amenities by category with availability status
 */
export function PropertyAmenitiesDetail({ amenities = [] }: PropertyAmenitiesDetailProps) {
  // Group amenities by category
  const groupedAmenities = amenities.reduce((acc, propertyAmenity) => {
    const category = propertyAmenity.amenity.category
    if (!acc[category.id]) {
      acc[category.id] = {
        category,
        amenities: [],
      }
    }
    acc[category.id].amenities.push(propertyAmenity)
    return acc
  }, {} as Record<number, { category: AmenityCategory; amenities: PropertyAmenity[] }>)

  const categories = Object.values(groupedAmenities).sort((a, b) => 
    a.category.sort_order - b.category.sort_order
  )

  if (amenities.length === 0) {
    return (
      <div className="property-amenities-detail property-amenities-detail--empty">
        <p className="property-amenities-detail-empty">No amenities information available</p>
      </div>
    )
  }

  return (
    <div className="property-amenities-detail">
      <h2 className="property-amenities-detail-title">Amenities</h2>
      
      {categories.map(({ category, amenities: categoryAmenities }) => (
        <div key={category.id} className="property-amenities-category">
          <h3 className="property-amenities-category-title">
            <span className="property-amenities-category-icon">{category.icon}</span>
            {category.name}
          </h3>
          
          <div className="property-amenities-list">
            {categoryAmenities
              .sort((a, b) => a.amenity.sort_order - b.amenity.sort_order)
              .map((propertyAmenity) => (
                <div 
                  key={propertyAmenity.amenity.id} 
                  className={`property-amenity-item ${
                    !propertyAmenity.is_available ? 'property-amenity-item--unavailable' : ''
                  }`}
                >
                  <div className="property-amenity-item-header">
                    <span className="property-amenity-item-icon">
                      {propertyAmenity.amenity.icon}
                    </span>
                    <span className="property-amenity-item-name">
                      {propertyAmenity.amenity.name}
                    </span>
                    {!propertyAmenity.is_available && (
                      <span className="property-amenity-item-status">
                        Not available
                      </span>
                    )}
                  </div>
                  
                  {propertyAmenity.amenity.description && (
                    <p className="property-amenity-item-description">
                      {propertyAmenity.amenity.description}
                    </p>
                  )}
                  
                  {propertyAmenity.notes && (
                    <p className="property-amenity-item-notes">
                      Note: {propertyAmenity.notes}
                    </p>
                  )}
                </div>
              ))}
          </div>
        </div>
      ))}
    </div>
  )
}