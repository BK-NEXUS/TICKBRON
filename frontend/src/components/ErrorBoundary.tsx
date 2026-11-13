import { ErrorFallback } from './ErrorFallback'
import { Component, ErrorInfo, ReactNode } from 'react'

interface ErrorBoundaryProps {
  children: ReactNode
  fallback?: ReactNode
}

interface ErrorBoundaryState {
  hasError: boolean
  error?: Error
}

/**
 * React komponent qátelikların tutıw hám islew ushın ErrorBoundary komponenti
 * Komponent aǵashları qátelik kótergende fallback UI beredi
 * Pútkil ilovanıń qulawınıń aldın aladı hám paydalanıwshı tájiriybesin jaqsılaydı
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Development te qátelikti konsolǵa jazıw
    if (import.meta.env.DEV) {
      console.error('ErrorBoundary caught an error:', error, errorInfo)
    }
    // Production ta buni qátelik izlew xızmetine jiberiwge boladı
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return <ErrorFallback />
    }

    return this.props.children
  }
}
