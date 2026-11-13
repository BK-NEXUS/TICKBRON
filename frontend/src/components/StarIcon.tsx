import { Star } from 'lucide-react'

/**
 * Átirapındaǵı tekst reńindegi toltırılǵan juldız; juldız tekst belgisin almastıradı, ayırım platformalar onı emoji retinde
 * sızadı.
 */
export function StarIcon({ size = 14 }: { size?: number }) {
  return <Star className="star-icon" size={size} fill="currentColor" strokeWidth={0} aria-hidden="true" />
}
