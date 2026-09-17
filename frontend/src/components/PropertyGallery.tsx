import { useState } from 'react'
import { Property } from '../adapters/searchAdapter'

interface PropertyGalleryProps {
  property: Property
}

/**
 * PropertyGallery component for displaying property images with navigation
 * Supports thumbnail navigation and responsive layout
 */
export function PropertyGallery({ property }: PropertyGalleryProps) {
  const [currentIndex, setCurrentIndex] = useState(0)
  
  // Mock gallery images - in real implementation, these would come from the property
  const galleryImages = [
    property.image_url || '🏠',
    property.image_url || '🏠',
    property.image_url || '🏠',
    property.image_url || '🏠',
    property.image_url || '🏠',
  ]

  const goToPrevious = () => {
    setCurrentIndex((prev) => (prev === 0 ? galleryImages.length - 1 : prev - 1))
  }

  const goToNext = () => {
    setCurrentIndex((prev) => (prev === galleryImages.length - 1 ? 0 : prev + 1))
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
          disabled={galleryImages.length <= 1}
        >
          ‹
        </button>
        
        <div className="property-gallery-image">
          <div className="property-gallery-image-placeholder">
            {galleryImages[currentIndex]}
          </div>
        </div>

        <button
          className="property-gallery-nav property-gallery-nav--next"
          onClick={goToNext}
          aria-label="Next image"
          disabled={galleryImages.length <= 1}
        >
          ›
        </button>
      </div>

      {galleryImages.length > 1 && (
        <div className="property-gallery-thumbnails">
          {galleryImages.map((image, index) => (
            <button
              key={index}
              className={`property-gallery-thumbnail ${
                index === currentIndex ? 'property-gallery-thumbnail--active' : ''
              }`}
              onClick={() => selectImage(index)}
              aria-label={`View image ${index + 1}`}
              aria-pressed={index === currentIndex}
            >
              <div className="property-gallery-thumbnail-placeholder">
                {image}
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}