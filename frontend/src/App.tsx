import { useI18n } from './i18n/I18nContext'
import { lazy, Suspense } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { ThemeProvider } from './theme/ThemeContext'
import { I18nProvider } from './i18n/I18nContext'
import { AuthProvider } from './contexts/AuthContext'
import { MainLayout } from './layout/MainLayout'
import { ErrorBoundary } from './components/ErrorBoundary'
import { RequireAccess } from './components/RequireAccess'
import { canUseAdminPanel, canUsePartnerPanel } from './utils/roles'

// Lazy load pages for code splitting and performance optimization
const HomePage = lazy(() => import('./pages/HomePage'))
const SearchResultsPage = lazy(() => import('./pages/SearchResultsPage'))
const PropertyDetailPage = lazy(() => import('./pages/PropertyDetailPage'))
const BookingPage = lazy(() => import('./pages/BookingPage'))
const LoginPage = lazy(() => import('./pages/LoginPage'))
const RegisterPage = lazy(() => import('./pages/RegisterPage'))
const BookingsPage = lazy(() => import('./pages/BookingsPage'))
const FavoritesPage = lazy(() => import('./pages/FavoritesPage'))
const ProfilePage = lazy(() => import('./pages/ProfilePage'))
const PartnerDashboardPage = lazy(() => import('./pages/PartnerDashboardPage'))
const AdminDashboardPage = lazy(() => import('./pages/AdminDashboardPage'))
const AdminCustomerProfile = lazy(() => import('./components/AdminCustomerProfile'))
const SupportLookupPage = lazy(() => import('./pages/SupportLookupPage'))
const NotFoundPage = lazy(() => import('./pages/NotFoundPage'))
const InfoPage = lazy(() => import('./pages/InfoPage'))
const DestinationsPage = lazy(() => import('./pages/DestinationsPage'))

// Loading component for Suspense fallback
function PageLoader() {
  const { t } = useI18n()
  return <div className="page-loader">{t('common.loading')}</div>
}

function App() {
  return (
    <ThemeProvider>
      <I18nProvider>
        <ErrorBoundary>
          <AuthProvider>
            <Router>
              <Suspense fallback={<PageLoader />}>
                <Routes>
                  <Route path="/" element={<MainLayout />}>
                    <Route index element={<HomePage />} />
                    <Route path="search" element={<SearchResultsPage />} />
                    <Route path="property/:id" element={<PropertyDetailPage />} />
                    <Route path="booking" element={<BookingPage />} />
                    <Route path="bookings" element={<BookingsPage />} />
                    <Route path="favorites" element={<FavoritesPage />} />
                    <Route path="profile" element={<ProfilePage />} />
                    <Route element={<RequireAccess allow={canUsePartnerPanel} area="partner" />}>
                      <Route path="partner" element={<PartnerDashboardPage />} />
                    </Route>
                    <Route element={<RequireAccess allow={canUseAdminPanel} area="admin" />}>
                      <Route path="admin" element={<AdminDashboardPage />} />
                      <Route path="admin/customers/:customerId" element={<AdminCustomerProfile />} />
                      <Route path="admin/support" element={<SupportLookupPage />} />
                    </Route>
                    <Route path="destinations" element={<DestinationsPage />} />
                    {(['about', 'help', 'contact', 'safety', 'terms', 'privacy', 'cookies'] as const).map(slug => (
                      <Route key={slug} path={slug} element={<InfoPage slug={slug} />} />
                    ))}
                    <Route path="*" element={<NotFoundPage />} />
                  </Route>
                  <Route path="/login" element={<LoginPage />} />
                  <Route path="/register" element={<RegisterPage />} />
                </Routes>
              </Suspense>
            </Router>
          </AuthProvider>
        </ErrorBoundary>
      </I18nProvider>
    </ThemeProvider>
  )
}

export default App
