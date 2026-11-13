import { useMemo } from 'react'
import QRCode from 'qrcode'

interface QrCodeProps {
  value: string
  /** Ekran oqıwshı súwret haqqında ne aytadı */
  label: string
}

// Skannerlerge kodtıń átirapında 4 moduldiń bos shegarası kerek
const QUIET_ZONE = 4

/** Brauzerde inline SVG retinde sızılǵan QR kod: tekst hesh qashan betten shıqpaydı (súwret xızmeti joq, data URL joq). */
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
      {/* Hárdayım aq fonda qara kvadratlar, qarańǵı temada da: skannerler jaqtı fonda qaranı kútedi */}
      <rect width={size} height={size} fill="#fff" />
      <path d={path} fill="#000" />
    </svg>
  )
}
