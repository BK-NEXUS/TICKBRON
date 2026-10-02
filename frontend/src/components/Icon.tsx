import { type LucideIcon } from 'lucide-react';

interface IconProps {
  /** The Lucide icon component to render */
  icon: LucideIcon;
  /** Icon size in pixels (default: 20) */
  size?: number;
  /** Additional CSS classes */
  className?: string;
  /** aria-label for accessibility */
  'aria-label'?: string;
  /** Whether the icon is purely decorative */
  decorative?: boolean;
}

/**
 * Wrapper component for Lucide icons to ensure consistent sizing and styling.
 * All icons in the app should use this component instead of raw Lucide imports.
 */
export function Icon({ icon: IconComponent, size = 20, className = '', 'aria-label': ariaLabel, decorative = false }: IconProps) {
  return (
    <IconComponent
      size={size}
      className={className}
      aria-hidden={decorative}
      aria-label={decorative ? undefined : ariaLabel}
      strokeWidth={2}
    />
  );
}