import type { MessageKey } from '../i18n/messages/en'
import { imageSizeProblem, type ImageRuleKind } from './imageRules'
import { readImageSize } from './imageSize'

// Same limits as the backend (`common.image_rules`); the server checks again.
export const MAX_IMAGE_BYTES = 10 * 1024 * 1024
const IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp']
const IMAGE_EXTENSIONS = /\.(jpe?g|png|webp)$/i

/** The message key for what is wrong with the type or the file size of a chosen picture, or null when it can be sent */
export function imageFileError(file: File): MessageKey | null {
  if (!IMAGE_TYPES.includes(file.type) || !IMAGE_EXTENSIONS.test(file.name)) return 'geoAdmin.errImageType'
  if (file.size > MAX_IMAGE_BYTES) return 'geoAdmin.errImageSize'
  return null
}

/** A message with the values to put in it */
export interface ImageProblem {
  key: MessageKey
  params?: Record<string, string | number>
}

/**
 * Everything the browser can tell about a chosen picture before it is sent: type, file size, then width and height
 * against the rule of the place. When the browser cannot read the picture the server decides.
 */
export async function imageProblem(file: File, kind: ImageRuleKind): Promise<ImageProblem | null> {
  const fileError = imageFileError(file)
  if (fileError) return { key: fileError }
  const size = await readImageSize(file)
  return size ? imageSizeProblem(size, kind) : null
}
