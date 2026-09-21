import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import { MainLayout } from './layout/MainLayout'
import { HomePage } from './pages/HomePage'
import { SearchResultsPage } from './pages/SearchResultsPage'
import { PropertyDetailPage } from './pages/PropertyDetailPage'
import { BookingPage } from './pages/BookingPage'
import { LoginPage } from './pages/LoginPage'
import { RegisterPage } from './pages/RegisterPage'
import { BookingsPage } from './pages/BookingsPage'
import { FavoritesPage } from './pages/FavoritesPage'
import { ProfilePage } from './pages/ProfilePage'
import { PartnerDashboardPage } from './pages/PartnerDashboardPage'
import { AdminDashboardPage } from './pages/AdminDashboardPage'
import { NotFoundPage } from './pages/NotFoundPage'

function App() {
  return (
    <AuthProvider>
      <Router>
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
      </Router>
    </AuthProvider>
  )
}

export default App
