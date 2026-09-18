import { useState } from 'react'
import { Property } from '../adapters/propertyAdapter'

interface PropertyGalleryProps {
  property: Property
}

/**
 * PropertyGallery component for displaying property images with navigation
 * Supports thumbnail navigation and responsive layout
 */
export function PropertyGallery({ property }: PropertyGalleryProps) {
  const [currentIndex, setCurrentIndex] = useState(0)
  
  // Get gallery images from property.gallery organized by photo type
  const galleryImages = property.gallery ? 
    Object.values(property.gallery).flat().sort((a, b) => a.display_order - b.display_order) :
    (property.primary_photo ? [property.primary_photo] : [])
  
  // Fallback to placeholder if no images
  const displayImages = galleryImages.length > 0 ? 
    galleryImages : 
    [{ id: 0, photo: '🏠', photo_type: 'other', is_primary: true, display_order: 0 }]

  const goToPrevious = () => {
    setCurrentIndex((prev) => (prev === 0 ? displayImages.length - 1 : prev - 1))
  }

  const goToNext = () => {
    setCurrentIndex((prev) => (prev === displayImages.length - 1 ? 0 : prev + 1))
  }

  const selectImage = (index: number) => {
    setCurrentIndex(index)
  }

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'ArrowLeft') {
      goToPrevious()
    } else if (event.key === 'ArrowRight') {
      goToNext()
    }
  }

  return (
    <div 
      className="property-gallery"
      onKeyDown={handleKeyDown}
      role="region"
      aria-label="Property image gallery"
    >
      <div className="property-gallery-main">
        <button
          className="property-gallery-nav property-gallery-nav--prev"
          onClick={goToPrevious}
          aria-label="Previous image"
          disabled={displayImages.length <= 1}
        >
          ‹
        </button>
        
        <div className="property-gallery-image">
          <div className="property-gallery-image-placeholder">
            {displayImages[currentIndex].photo}
          </div>
        </div>

        <button
          className="property-gallery-nav property-gallery-nav--next"
          onClick={goToNext}
          aria-label="Next image"
          disabled={displayImages.length <= 1}
        >
          ›
        </button>
      </div>

      {displayImages.length > 1 && (
        <div className="property-gallery-thumbnails">
          {displayImages.map((image, index) => (
            <button
              key={image.id}
              className={`property-gallery-thumbnail ${
                index === currentIndex ? 'property-gallery-thumbnail--active' : ''
              }`}
              onClick={() => selectImage(index)}
              aria-label={`View image ${index + 1}`}
              aria-pressed={index === currentIndex}
            >
              <div className="property-gallery-thumbnail-placeholder">
                {image.photo}
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}