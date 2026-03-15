import React from 'react'
import { Button } from '@/components/ui/button'
import { Copy } from 'lucide-react'
import { toast } from 'sonner'

interface Props {
  children: React.ReactNode
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void
}

interface State {
  hasError: boolean
  error: Error | null
  errorId: string | null
}

// Class component is intentional: React's error boundary API (getDerivedStateFromError /
// componentDidCatch) has no functional equivalent and requires a class component.
export class ErrorBoundary extends React.Component<Props, State> {
  state: State = { hasError: false, error: null, errorId: null }

  static getDerivedStateFromError(error: Error): Partial<State> {
    const errorId = `error-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    return { hasError: true, error, errorId }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo)
    console.error('Error ID:', this.state.errorId)

    if (this.props.onError) {
      this.props.onError(error, errorInfo)
    }
  }

  copyErrorDetails = () => {
    const errorDetails = `Error ID: ${this.state.errorId}\nError: ${this.state.error?.message}\nStack: ${this.state.error?.stack}`
    navigator.clipboard
      .writeText(errorDetails)
      .then(() => toast.success('Error details copied to clipboard'))
      .catch(() => toast.error('Failed to copy error details'))
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-screen flex-col items-center justify-center gap-4 p-4">
          <div className="text-center space-y-4 max-w-lg">
            <h1 className="text-2xl font-bold">Something went wrong</h1>
            <p className="text-muted-foreground">{this.state.error?.message}</p>
            {this.state.errorId && (
              <p className="text-xs text-muted-foreground font-mono">
                Error ID: {this.state.errorId}
              </p>
            )}
            <div className="flex gap-2 justify-center">
              <Button onClick={() => this.setState({ hasError: false, error: null, errorId: null })}>
                Try again
              </Button>
              <Button variant="outline" onClick={this.copyErrorDetails}>
                <Copy className="h-4 w-4 mr-2" />
                Copy error details
              </Button>
            </div>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}
