/**
 * Blobtı waqtınsha silteme arqalı fayl retinde saqlaydı (maǵlıwmat apiFetch penen alınǵan, sol sebepli auth aldınan
 * qollanılǵan)
 */
export function saveBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}
