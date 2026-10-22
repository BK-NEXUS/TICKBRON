import type { MessageKey } from '../i18n/messages/en'

// Same limits as the backend (`common.storage.validate_image_file`); the server checks again.
export const MAX_IMAGE_BYTES = 10 * 1024 * 1024
const IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
const IMAGE_EXTENSIONS = /\.(jpe?g|png|webp|gif)$/i

/** The message key for what is wrong with a chosen picture, or null when it can be sent */
export function imageFileError(file: File): MessageKey | null {
  if (!IMAGE_TYPES.includes(file.type) || !IMAGE_EXTENSIONS.test(file.name)) return 'geoAdmin.errImageType'
  if (file.size > MAX_IMAGE_BYTES) return 'geoAdmin.errImageSize'
  return null
}
