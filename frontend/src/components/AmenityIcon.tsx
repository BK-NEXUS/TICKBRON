import {
  ArrowUpDown, BellRing, BriefcaseMedical, Car, DoorOpen, Flame, ShieldCheck, ShowerHead, Snowflake,
  Sparkles, Trees, Tv, Utensils, WashingMachine, Wifi, type LucideIcon,
} from 'lucide-react'

// Icons are chosen by slug, never from the stored icon text: that field is free text an admin can type.
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

/** Decorative icon of an amenity, category or feature filter; unknown slugs get a neutral icon. */
export function AmenityIcon({ slug, size = 18 }: { slug: string; size?: number }) {
  const Icon = ICONS[slug] ?? Sparkles
  return <Icon size={size} aria-hidden="true" />
}
