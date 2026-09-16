import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { MainLayout } from './layout/MainLayout'
import { HomePage } from './pages/HomePage'
import { SearchResultsPage } from './pages/SearchResultsPage'
import { NotFoundPage } from './pages/NotFoundPage'

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<HomePage />} />
          <Route path="search" element={<SearchResultsPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </Router>
  )
}

export default App
