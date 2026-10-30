import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router'
import { TwoFactorSetupPage } from './TwoFactorSetupPage'
import { TwoFactorSetupGate } from '../components/TwoFactorSetupGate'
import { AuthProvider } from '../contexts/AuthContext'
import { I18nProvider } from '../i18n/I18nContext'
import { authAdapter, type User } from '../adapters/authAdapter'
import { saveBlob } from '../utils/saveBlob'

vi.mock('../adapters/authAdapter', () => ({
  authAdapter: {
    getCurrentUser: vi.fn(),
    startTwoFactorSetup: vi.fn(),
    confirmTwoFactorSetup: vi.fn(),
    logout: vi.fn(),
  },
}))
vi.mock('../utils/saveBlob', () => ({ saveBlob: vi.fn() }))

const QR_LABEL = 'QR code for the authenticator app'
const getCurrentUser = vi.mocked(authAdapter.getCurrentUser)
const start = vi.mocked(authAdapter.startTwoFactorSetup)
const confirm = vi.mocked(authAdapter.confirmTwoFactorSetup)

const admin = (extra: Partial<User> = {}): User => ({
  id: 1, email: 'admin@example.com', is_staff: true, is_superuser: true, two_factor_enabled: false,
  two_factor_setup_required: true, ...extra,
} as User)

async function renderAt(path: string) {
  render(
    <I18nProvider>
      <AuthProvider>
        <MemoryRouter initialEntries={[path]}>
          <TwoFactorSetupGate>
            <Routes>
              <Route path="/" element={<div>Home page</div>} />
              <Route path="/admin" element={<div>Admin page</div>} />
              <Route path="/login" element={<div>Login page</div>} />
              <Route path="/two-factor-setup" element={<TwoFactorSetupPage />} />
            </Routes>
          </TwoFactorSetupGate>
        </MemoryRouter>
      </AuthProvider>
    </I18nProvider>,
  )
  await act(async () => {})
}

describe('two-step setup', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    getCurrentUser.mockResolvedValue({ success: true, user: admin() })
    start.mockResolvedValue({ success: true, otpauthUri: 'otpauth://totp/TICKBRON:a?secret=JBSWY3DP', secret: 'JBSWY3DP' })
  })

  it('sends an administrator who must set it up to the setup page, from anywhere', async () => {
    await renderAt('/')

    expect(await screen.findByRole('heading', { name: 'Set up two-step sign-in' })).toBeInTheDocument()
  })

  it('shows the QR code, the secret as text, and asks for the secret only once', async () => {
    await renderAt('/two-factor-setup')

    expect(await screen.findByRole('img', { name: QR_LABEL })).toBeInTheDocument()
    expect(screen.getByText('JBSWY3DP')).toBeInTheDocument()
    expect(start).toHaveBeenCalledTimes(1)
  })

  it('sends a visitor who is not signed in to the login page', async () => {
    getCurrentUser.mockResolvedValue({ success: false })
    await renderAt('/two-factor-setup')

    expect(await screen.findByText('Login page')).toBeInTheDocument()
    expect(start).not.toHaveBeenCalled()
  })

  it('says why the setup could not start and lets the person try again', async () => {
    start.mockResolvedValueOnce({ success: false, error: 'Offline' })
    await renderAt('/two-factor-setup')

    expect(await screen.findByRole('alert')).toHaveTextContent('Offline')
    fireEvent.click(screen.getByRole('button', { name: 'Try again' }))

    expect(await screen.findByRole('img', { name: QR_LABEL })).toBeInTheDocument()
  })

  it('refuses an empty code without calling the server', async () => {
    await renderAt('/two-factor-setup')
    await screen.findByRole('img', { name: QR_LABEL })

    fireEvent.click(screen.getByRole('button', { name: 'Switch on' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Enter the 6-digit code.')
    expect(confirm).not.toHaveBeenCalled()
  })

  it('shows the server refusal for a wrong code and stays on the scan step', async () => {
    confirm.mockResolvedValue({ success: false, error: 'The code is not right.' })
    await renderAt('/two-factor-setup')
    await screen.findByRole('img', { name: QR_LABEL })

    fireEvent.change(screen.getByLabelText('6-digit code'), { target: { value: '000000' } })
    fireEvent.click(screen.getByRole('button', { name: 'Switch on' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('The code is not right.')
    expect(screen.getByRole('img', { name: QR_LABEL })).toBeInTheDocument()
  })

  it('shows the backup codes once, lets them be downloaded, and needs the "saved" tick to go on', async () => {
    confirm.mockResolvedValue({ success: true, backupCodes: ['ab12c-34d56', 'ef78g-90h12'] })
    await renderAt('/two-factor-setup')
    await screen.findByRole('img', { name: QR_LABEL })
    // The account now has it on: the page must stay open for the backup codes
    getCurrentUser.mockResolvedValue({ success: true, user: admin({ two_factor_enabled: true, two_factor_setup_required: false }) })

    fireEvent.change(screen.getByLabelText('6-digit code'), { target: { value: '123456' } })
    fireEvent.click(screen.getByRole('button', { name: 'Switch on' }))

    expect(await screen.findByText('ab12c-34d56')).toBeInTheDocument()
    expect(screen.getByText('ef78g-90h12')).toBeInTheDocument()
    expect(confirm).toHaveBeenCalledWith('123456')

    fireEvent.click(screen.getByRole('button', { name: 'Download' }))
    expect(saveBlob).toHaveBeenCalledTimes(1)

    const next = screen.getByRole('button', { name: 'Continue' })
    expect(next).toBeDisabled()
    fireEvent.click(screen.getByLabelText('I saved these codes'))
    expect(next).toBeEnabled()
    fireEvent.click(next)

    await waitFor(() => expect(screen.getByText('Admin page')).toBeInTheDocument())
  })

  it('leaves an account that already has it on alone', async () => {
    getCurrentUser.mockResolvedValue({ success: true, user: admin({ two_factor_enabled: true, two_factor_setup_required: false }) })
    await renderAt('/two-factor-setup')

    expect(await screen.findByText('Home page')).toBeInTheDocument()
    expect(start).not.toHaveBeenCalled()
  })

  it('lets the person sign out instead of finishing', async () => {
    vi.mocked(authAdapter.logout).mockResolvedValue({ success: true })
    await renderAt('/two-factor-setup')
    await screen.findByRole('img', { name: QR_LABEL })

    fireEvent.click(screen.getByRole('button', { name: 'Sign out' }))

    expect(await screen.findByText('Login page')).toBeInTheDocument()
  })
})
