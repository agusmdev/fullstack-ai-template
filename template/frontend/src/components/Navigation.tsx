import { Link, useNavigate } from '@tanstack/react-router'
import { useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { useAuth } from '@/contexts/AuthContext'

export default function Navigation() {
  const { isAuthenticated, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = useCallback(async () => {
    await logout()
    navigate({ to: '/login' })
  }, [logout, navigate])

  return (
    <header className="nav-header">
      <nav className="nav-container">
        <div className="nav-content">
          <div className="nav-left">
            <Link to="/" className="nav-logo">
              <span className="nav-logo-bracket">[</span>
              <span className="nav-logo-text">FST</span>
              <span className="nav-logo-bracket">]</span>
            </Link>
            <div className="nav-links">
              <Link
                to="/"
                className="nav-link"
                activeProps={{ className: 'nav-link-active' }}
              >
                Home
              </Link>
              {isAuthenticated && (
                <Link
                  to="/items"
                  className="nav-link"
                  activeProps={{ className: 'nav-link-active' }}
                >
                  Items
                </Link>
              )}
            </div>
          </div>
          <div className="nav-actions">
            {isAuthenticated ? (
              <Button
                onClick={handleLogout}
                variant="outline"
                className="nav-logout-btn"
              >
                Logout
              </Button>
            ) : (
              <>
                <Link to="/login" className="nav-login">
                  Login
                </Link>
                <Link to="/register" className="nav-signup">
                  Sign Up
                </Link>
              </>
            )}
          </div>
        </div>
      </nav>
    </header>
  )
}
