import type { ImageSize } from './imageRules'

/** Súwret elementi hám blob mánzili arqalı: createImageBitmap joq brauzer ushın */
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
 * Tańlanǵan súwrettiń brauzer kórsetkenindey eni hám boyı (jantaytıp saqlanǵan telefon súwreti aldınan burılǵan),
 * yamasa brauzer oqıy almasa null. createImageBitmap fayldıń ózin ashadı, sol sebepli bettiń siyasatı súwretler ushın
 * biykar etiwi múmkin blob mánzili kerek emes. Ekranlar testleri súwretti ashpastan juwap bere alıwı ushın bólek saqlanǵan.
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
