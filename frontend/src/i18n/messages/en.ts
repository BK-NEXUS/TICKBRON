export const en = {
  'nav.home': 'Home',
  'nav.properties': 'Properties',
  'nav.about': 'About',
  'nav.help': 'Help',
  'header.openMenu': 'Open menu',
  'header.account': 'Account',
  'header.login': 'Login',
  'header.signUp': 'Sign Up',
  'header.signOut': 'Sign Out',
  'header.myProfile': 'My Profile',
  'header.myBookings': 'My Bookings',
  'header.favorites': 'Favorites',
  'header.partnerDashboard': 'Partner Dashboard',
  'header.adminDashboard': 'Admin Dashboard',
  'language.label': 'Language: {name}',
  'currency.label': 'Currency: {name}',
  'currency.UZS': 'Uzbek sum',
  'currency.USD': 'US dollar',
} as const

export type MessageKey = keyof typeof en
