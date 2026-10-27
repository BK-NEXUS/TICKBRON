import { useMemo } from 'react'
import { partnerAdapter } from '../adapters/partnerAdapter'
import type { PhotoApi } from '../adapters/partnerAdapter'
import { PartnerPhotoManager } from './PartnerPhotoManager'

interface PartnerPhotosManagementProps {
  propertyId: number
}

// Same as MAX_PHOTOS_PER_PROPERTY on the backend
const MAX_PHOTOS = 50

/** The photos of one hotel (owner panel > Photos). */
export function PartnerPhotosManagement({ propertyId }: PartnerPhotosManagementProps) {
  const api = useMemo<PhotoApi>(() => ({
    list: () => partnerAdapter.getPropertyPhotos(propertyId),
    upload: data => partnerAdapter.uploadPropertyPhoto(propertyId, data),
    update: (photoId, data) => partnerAdapter.updatePropertyPhoto(propertyId, photoId, data),
    remove: photoId => partnerAdapter.deletePropertyPhoto(propertyId, photoId),
  }), [propertyId])
  return (
    <PartnerPhotoManager
      api={api} max={MAX_PHOTOS} idPrefix="partner-photos" titleKey="photos.title" emptyHintKey="photos.emptyHint"
    />
  )
}
