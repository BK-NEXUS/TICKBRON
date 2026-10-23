import { useMemo } from 'react'
import { partnerAdapter } from '../adapters/partnerAdapter'
import type { PhotoApi } from '../adapters/partnerAdapter'
import { PartnerPhotoManager } from './PartnerPhotoManager'

interface PartnerRoomPhotosProps {
  roomTypeId: number
}

// Same as MAX_PHOTOS_PER_ROOM_TYPE on the backend
export const MAX_ROOM_PHOTOS = 20

/** The photos of one room type (inside the room form). */
export function PartnerRoomPhotos({ roomTypeId }: PartnerRoomPhotosProps) {
  const api = useMemo<PhotoApi>(() => ({
    list: () => partnerAdapter.getRoomPhotos(roomTypeId),
    upload: data => partnerAdapter.uploadRoomPhoto(roomTypeId, data),
    update: (photoId, data) => partnerAdapter.updateRoomPhoto(roomTypeId, photoId, data),
    remove: photoId => partnerAdapter.deleteRoomPhoto(roomTypeId, photoId),
  }), [roomTypeId])
  return (
    <PartnerPhotoManager
      api={api} max={MAX_ROOM_PHOTOS} idPrefix="room-photos" titleKey="roomPhotos.title" emptyHintKey="roomPhotos.emptyHint"
      headingLevel={3}
    />
  )
}
