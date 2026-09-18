import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { MainLayout } from './layout/MainLayout'
import { HomePage } from './pages/HomePage'
import { SearchResultsPage } from './pages/SearchResultsPage'
import { PropertyDetailPage } from './pages/PropertyDetailPage'
import { BookingsPage } from './pages/BookingsPage'
import { FavoritesPage } from './pages/FavoritesPage'
import { ProfilePage } from './pages/ProfilePage'
import { NotFoundPage } from './pages/NotFoundPage'

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<HomePage />} />
          <Route path="search" element={<SearchResultsPage />} />
          <Route path="property/:id" element={<PropertyDetailPage />} />
          <Route path="bookings" element={<BookingsPage />} />
          <Route path="favorites" element={<FavoritesPage />} />
          <Route path="profile" element={<ProfilePage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </Router>
  )
}

export default App
