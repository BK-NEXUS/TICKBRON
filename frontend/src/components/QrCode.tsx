import { useMemo } from 'react'
import QRCode from 'qrcode'

interface QrCodeProps {
  value: string
  /** What a screen reader says about the picture */
  label: string
}

// Scanners need an empty border of 4 modules around the code
const QUIET_ZONE = 4

/** A QR code drawn as an inline SVG in the browser: the text never leaves the page (no image service, no data URL). */
export function QrCode({ value, label }: QrCodeProps) {
  const { size, path } = useMemo(() => {
    const { modules } = QRCode.create(value, { errorCorrectionLevel: 'M' })
    const squares: string[] = []
    for (let row = 0; row < modules.size; row += 1) {
      for (let column = 0; column < modules.size; column += 1) {
        if (modules.get(row, column)) squares.push(`M${column + QUIET_ZONE} ${row + QUIET_ZONE}h1v1h-1z`)
      }
    }
    return { size: modules.size + 2 * QUIET_ZONE, path: squares.join('') }
  }, [value])

  return (
    <svg className="qr-code" viewBox={`0 0 ${size} ${size}`} role="img" aria-label={label} shapeRendering="crispEdges">
      {/* Always white with black squares, also in the dark theme: scanners expect dark on light */}
      <rect width={size} height={size} fill="#fff" />
      <path d={path} fill="#000" />
    </svg>
  )
}
