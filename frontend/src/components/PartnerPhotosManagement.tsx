import { useMemo } from 'react'
import { partnerAdapter } from '../adapters/partnerAdapter'
import type { PhotoApi } from '../adapters/partnerAdapter'
import { PartnerPhotoManager } from './PartnerPhotoManager'

interface PartnerPhotosManagementProps {
  propertyId: number
}

// Backend degi MAX_PHOTOS_PER_PROPERTY penen birdey
const MAX_PHOTOS = 50

/** Bir mehmanxananıń súwretleri (iye paneli > Súwretler). */
export function PartnerPhotosManagement({ propertyId }: PartnerPhotosManagementProps) {
  const api = useMemo<PhotoApi>(() => ({
    list: () => partnerAdapter.getPropertyPhotos(propertyId),
    upload: data => partnerAdapter.uploadPropertyPhoto(propertyId, data),
    update: (photoId, data) => partnerAdapter.updatePropertyPhoto(propertyId, photoId, data),
    remove: photoId => partnerAdapter.deletePropertyPhoto(propertyId, photoId),
  }), [propertyId])
  return (
    <PartnerPhotoManager
      imageKind="hotel"
      api={api} max={MAX_PHOTOS} idPrefix="partner-photos" titleKey="photos.title" emptyHintKey="photos.emptyHint"
    />
  )
}
