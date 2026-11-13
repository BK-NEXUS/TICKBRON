import type { MessageKey } from '../i18n/messages/en'
import { imageSizeProblem, type ImageRuleKind } from './imageRules'
import { readImageSize } from './imageSize'

// Backend penen birdey shekler (`common.image_rules`); server qayta tekseredi.
export const MAX_IMAGE_BYTES = 10 * 1024 * 1024
const IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp']
const IMAGE_EXTENSIONS = /\.(jpe?g|png|webp)$/i

/**
 * Tańlanǵan súwrettiń túri yamasa fayl ólshemi menen ne qátelik ekenin bildiretuǵın xabar kilti, yamasa jiberiw múmkin bolsa
 * null
 */
export function imageFileError(file: File): MessageKey | null {
  if (!IMAGE_TYPES.includes(file.type) || !IMAGE_EXTENSIONS.test(file.name)) return 'geoAdmin.errImageType'
  if (file.size > MAX_IMAGE_BYTES) return 'geoAdmin.errImageSize'
  return null
}

/** Ishine qoyılatuǵın mánisleri bar xabar */
export interface ImageProblem {
  key: MessageKey
  params?: Record<string, string | number>
}

/**
 * Jiberilmesten aldın brauzer tańlanǵan súwret haqqında ayta alatuǵın hámme nárse: túri, fayl ólshemi, keyin eni hám boyı
 * orınnıń qaǵıydasına qarata. Brauzer súwretti oqıy almasa server sheshedi.
 */
export async function imageProblem(file: File, kind: ImageRuleKind): Promise<ImageProblem | null> {
  const fileError = imageFileError(file)
  if (fileError) return { key: fileError }
  const size = await readImageSize(file)
  return size ? imageSizeProblem(size, kind) : null
}
