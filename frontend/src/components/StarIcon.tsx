import { Star } from 'lucide-react'

/** Filled star in the colour of the surrounding text; replaces the star text character, which some platforms draw as an emoji. */
export function StarIcon({ size = 14 }: { size?: number }) {
  return <Star className="star-icon" size={size} fill="currentColor" strokeWidth={0} aria-hidden="true" />
}
