import {
  // Navigation
  Home,
  Menu,
  X,
  ChevronDown,
  ChevronRight,
  ChevronLeft,
  Search,
  Calendar,
  User,
  Heart,
  LogOut,
  Settings,
  // Property types
  Building,
  Home as House,
  Building2,
  // Amenities
  Wifi,
  Flame,
  Tv,
  Lock,
  TreePine,
  Utensils,
  ShowerHead,
  Sparkles,
  // Actions
  Copy,
  Check,
  CheckCircle,
  AlertCircle,
  XCircle,
  Loader,
  // Payment
  CreditCard,
  Smartphone,
  Wallet,
  Mail,
  Phone,
  // Status
  Shield,
  Ban,
  Users,
  UserCheck,
  BarChart,
  // Travel
  MapPin,
  Globe,
  Plane,
  Star,
  // Misc
  Globe as Earth,
  Smartphone as Mobile,
  Key,
  Eye,
  EyeOff,
  Bell,
  Filter,
  Grid,
  List,
  Map,
  // Form
  ChevronUp,
  Plus,
  Minus,
  Trash2,
  Edit,
  ArrowLeft,
  ArrowRight,
  Download,
  Upload,
  RefreshCw,
  ExternalLink,
  Link2,
  // Payment status
  CircleCheck,
  CircleX,
  Clock,
  HelpCircle,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

export type IconName =
  | 'home'
  | 'menu'
  | 'close'
  | 'chevron-down'
  | 'chevron-right'
  | 'chevron-left'
  | 'search'
  | 'calendar'
  | 'user'
  | 'heart'
  | 'logout'
  | 'settings'
  | 'building'
  | 'house'
  | 'building2'
  | 'wifi'
  | 'flame'
  | 'tv'
  | 'lock'
  | 'tree-pine'
  | 'utensils'
  | 'shower-head'
  | 'sparkles'
  | 'copy'
  | 'check'
  | 'check-circle'
  | 'alert-circle'
  | 'x-circle'
  | 'loader'
  | 'credit-card'
  | 'smartphone'
  | 'wallet'
  | 'mail'
  | 'phone'
  | 'shield'
  | 'ban'
  | 'users'
  | 'user-check'
  | 'bar-chart'
  | 'map-pin'
  | 'globe'
  | 'plane'
  | 'star'
  | 'earth'
  | 'mobile'
  | 'key'
  | 'eye'
  | 'eye-off'
  | 'bell'
  | 'filter'
  | 'grid'
  | 'list'
  | 'map'
  | 'chevron-up'
  | 'plus'
  | 'minus'
  | 'trash'
  | 'edit'
  | 'arrow-left'
  | 'arrow-right'
  | 'download'
  | 'upload'
  | 'refresh'
  | 'external-link'
  | 'link'
  | 'circle-check'
  | 'circle-x'
  | 'clock'
  | 'help-circle';

const iconMap: Record<IconName, LucideIcon> = {
  // Navigation
  home: Home,
  menu: Menu,
  close: X,
  'chevron-down': ChevronDown,
  'chevron-right': ChevronRight,
  'chevron-left': ChevronLeft,
  search: Search,
  calendar: Calendar,
  user: User,
  heart: Heart,
  logout: LogOut,
  settings: Settings,
  // Property types
  building: Building,
  house: House,
  building2: Building2,
  // Amenities
  wifi: Wifi,
  flame: Flame,
  tv: Tv,
  lock: Lock,
  'tree-pine': TreePine,
  utensils: Utensils,
  'shower-head': ShowerHead,
  sparkles: Sparkles,
  // Actions
  copy: Copy,
  check: Check,
  'check-circle': CheckCircle,
  'alert-circle': AlertCircle,
  'x-circle': XCircle,
  loader: Loader,
  // Payment
  'credit-card': CreditCard,
  smartphone: Smartphone,
  wallet: Wallet,
  mail: Mail,
  phone: Phone,
  // Status
  shield: Shield,
  ban: Ban,
  users: Users,
  'user-check': UserCheck,
  'bar-chart': BarChart,
  // Travel
  'map-pin': MapPin,
  globe: Globe,
  plane: Plane,
  star: Star,
  // Misc
  earth: Earth,
  mobile: Mobile,
  key: Key,
  eye: Eye,
  'eye-off': EyeOff,
  bell: Bell,
  filter: Filter,
  grid: Grid,
  list: List,
  map: Map,
  'chevron-up': ChevronUp,
  plus: Plus,
  minus: Minus,
  trash: Trash2,
  edit: Edit,
  'arrow-left': ArrowLeft,
  'arrow-right': ArrowRight,
  download: Download,
  upload: Upload,
  refresh: RefreshCw,
  'external-link': ExternalLink,
  link: Link2,
  // Payment status
  'circle-check': CircleCheck,
  'circle-x': CircleX,
  clock: Clock,
  'help-circle': HelpCircle,
};

/**
 * Get a Lucide icon component by name.
 * Use with the Icon component: <Icon icon={getIcon('home')} />
 */
export function getIcon(name: IconName): LucideIcon {
  return iconMap[name];
}