import { lazy, Suspense } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import { MainLayout } from './layout/MainLayout'
import { ErrorBoundary } from './components/ErrorBoundary'

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
const NotFoundPage = lazy(() => import('./pages/NotFoundPage'))

// Loading component for Suspense fallback
function PageLoader() {
  return (
    <div style={{ 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center', 
      minHeight: '100vh',
      fontSize: '18px',
      color: '#16262B'
    }}>
      Loading...
    </div>
  )
}

function App() {
  return (
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
                <Route path="partner" element={<PartnerDashboardPage />} />
                <Route path="admin" element={<AdminDashboardPage />} />
                <Route path="*" element={<NotFoundPage />} />
              </Route>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
            </Routes>
          </Suspense>
        </Router>
      </AuthProvider>
    </ErrorBoundary>
  )
}

export default App
