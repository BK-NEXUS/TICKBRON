import type { ImageSize } from './imageRules'

/** Through an image element and a blob address: for a browser without createImageBitmap */
function readWithImageElement(file: File): Promise<ImageSize | null> {
  return new Promise(resolve => {
    if (typeof URL.createObjectURL !== 'function') {
      resolve(null)
      return
    }
    const url = URL.createObjectURL(file)
    const image = new Image()
    const done = (size: ImageSize | null) => {
      URL.revokeObjectURL(url)
      resolve(size)
    }
    image.onload = () => done(image.naturalWidth > 0 && image.naturalHeight > 0 ? { width: image.naturalWidth, height: image.naturalHeight } : null)
    image.onerror = () => done(null)
    image.src = url
  })
}

/**
 * The width and height of a chosen picture as the browser shows it (a phone photo stored sideways is already turned),
 * or null when the browser cannot read it. createImageBitmap decodes the file itself, so it needs no blob address that
 * the page's policy could refuse for images. Kept apart so the screens' tests can answer it without decoding a picture.
 */
export async function readImageSize(file: File): Promise<ImageSize | null> {
  if (typeof createImageBitmap !== 'function') return readWithImageElement(file)
  try {
    const bitmap = await createImageBitmap(file)
    const size = { width: bitmap.width, height: bitmap.height }
    bitmap.close()
    return size
  } catch {
    return null
  }
}
