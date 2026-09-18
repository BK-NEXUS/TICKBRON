import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { authAdapter, User } from '../adapters/authAdapter'

interface AuthContextType {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>
  register: (data: {
    email: string
    first_name: string
    last_name: string
    phone_number?: string
    password: string
    password_confirm: string
  }) => Promise<{ success: boolean; error?: string }>
  logout: () => Promise<{ success: boolean; error?: string }>
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Check authentication status on mount
  useEffect(() => {
    const checkAuth = async () => {
      setIsLoading(true)
      try {
        const response = await authAdapter.getCurrentUser()
        if (response.success && response.user) {
          setUser(response.user)
        }
      } catch (error) {
        console.error('Failed to check auth status:', error)
      } finally {
        setIsLoading(false)
      }
    }

    checkAuth()
  }, [])

  const login = async (email: string, password: string) => {
    const response = await authAdapter.login({ email, password })
    if (response.success && response.user) {
      setUser(response.user)
    }
    return response
  }

  const register = async (data: {
    email: string
    first_name: string
    last_name: string
    phone_number?: string
    password: string
    password_confirm: string
  }) => {
    const response = await authAdapter.register(data)
    if (response.success && response.user) {
      setUser(response.user)
    }
    return response
  }

  const logout = async () => {
    const response = await authAdapter.logout()
    if (response.success) {
      setUser(null)
    }
    return response
  }

  const refreshUser = async () => {
    const response = await authAdapter.getCurrentUser()
    if (response.success && response.user) {
      setUser(response.user)
    } else {
      setUser(null)
    }
  }

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated: !!user,
    login,
    register,
    logout,
    refreshUser,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
