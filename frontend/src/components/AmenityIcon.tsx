import {
  ArrowUpDown, BellRing, BriefcaseMedical, Car, DoorOpen, Flame, ShieldCheck, ShowerHead, Snowflake,
  Sparkles, Trees, Tv, Utensils, WashingMachine, Wifi, type LucideIcon,
} from 'lucide-react'

// Ikonkalar slug boyınsha tańlanadı, hesh qashan saqlanǵan ikonka tekstinen emes: ol maydan admin teretuǵın erkin tekst.
const ICONS: Record<string, LucideIcon> = {
  wifi: Wifi,
  parking: Car,
  ac: Snowflake,
  heating: Flame,
  elevator: ArrowUpDown,
  kitchen: Utensils,
  bathroom: ShowerHead,
  entertainment: Tv,
  tv: Tv,
  safety: ShieldCheck,
  'smoke-alarm': BellRing,
  'first-aid': BriefcaseMedical,
  outdoor: Trees,
  balcony: DoorOpen,
  washer: WashingMachine,
}

/** Amenity, kategoriya yamasa feature filteriniń bezew ikonkası; belgisiz slug lar neytral ikonka aladı. */
export function AmenityIcon({ slug, size = 18 }: { slug: string; size?: number }) {
  const Icon = ICONS[slug] ?? Sparkles
  return <Icon size={size} aria-hidden="true" />
}
