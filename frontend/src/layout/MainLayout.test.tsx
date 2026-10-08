import { describe, it, expect, vi } from 'vitest'
import { act, render, screen } from '@testing-library/react'
import { readdirSync, readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { MainLayout } from './MainLayout'
import { AuthProvider } from '../contexts/AuthContext'

vi.mock('../adapters/authAdapter', () => ({
  authAdapter: {
    getCurrentUser: vi.fn().mockResolvedValue({ success: false }),
  },
}))

describe('MainLayout', () => {
  it('renders the header and the footer content inside the container', async () => {
    const { container } = render(
      <AuthProvider>
        <MemoryRouter initialEntries={['/page']}>
          <Routes>
            <Route element={<MainLayout />}>
              <Route path="/page" element={<p>Page body</p>} />
            </Route>
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    )
    await act(async () => {})

    expect(screen.getByText('Page body')).toBeInTheDocument()
    expect(container.querySelector('.header-container')).toHaveClass('container')
    expect(container.querySelector('.footer-container')).toHaveClass('container')
    expect(container.querySelector('.footer-bottom')).toHaveClass('container')
  })
})

describe('pages', () => {
  const pagesDir = resolve(__dirname, '../pages')
  const pages = readdirSync(pagesDir).filter((file) => /Page\.tsx$/.test(file))

  it.each(pages)('%s renders its content inside the container', (file) => {
    expect(readFileSync(resolve(pagesDir, file), 'utf-8')).toMatch(/className="[^"]*\bcontainer\b/)
  })
})
