import { Link, useNavigate } from '@tanstack/react-router'
import { useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { useAuth } from '@/contexts/AuthContext'

export function Navigation() {
  const { isAuthenticated, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = useCallback(async () => {
    await logout()
    navigate({ to: '/login' })
  }, [logout, navigate])

  return (
    <header className="fixed top-0 left-0 right-0 z-[1000] bg-[rgba(10,10,11,0.8)] backdrop-blur-[20px] border-b border-[rgba(46,46,50,0.5)]">
      <nav className="max-w-[1400px] mx-auto px-8">
        <div className="flex items-center justify-between h-[72px]">
          <div className="flex items-center gap-12">
            <Link
              to="/"
              className="flex items-center gap-1 text-2xl font-black text-[#EDEDEF] no-underline transition-all duration-150 ease-[cubic-bezier(0.4,0,0.2,1)] hover:-translate-y-px"
            >
              <span className="text-[#5E6AD2] font-bold">[</span>
              <span className="tracking-tight">FST</span>
              <span className="text-[#5E6AD2] font-bold">]</span>
            </Link>
            <div className="hidden md:flex items-center gap-8">
              <Link
                to="/"
                className="relative text-[15px] font-medium text-[#9394A1] no-underline transition-colors duration-150 py-2 hover:text-[#EDEDEF] after:content-[''] after:absolute after:bottom-0 after:left-0 after:h-0.5 after:w-0 after:bg-[#5E6AD2] after:transition-[width] after:duration-200 hover:after:w-full"
                activeProps={{ className: 'text-[#EDEDEF] after:w-full' }}
              >
                Home
              </Link>
              {isAuthenticated && (
                <Link
                  to="/items"
                  className="relative text-[15px] font-medium text-[#9394A1] no-underline transition-colors duration-150 py-2 hover:text-[#EDEDEF] after:content-[''] after:absolute after:bottom-0 after:left-0 after:h-0.5 after:w-0 after:bg-[#5E6AD2] after:transition-[width] after:duration-200 hover:after:w-full"
                  activeProps={{ className: 'text-[#EDEDEF] after:w-full' }}
                >
                  Items
                </Link>
              )}
            </div>
          </div>
          <div className="flex items-center gap-4">
            {isAuthenticated ? (
              <Button
                onClick={handleLogout}
                variant="outline"
                className="text-[15px] font-medium rounded-lg"
              >
                Logout
              </Button>
            ) : (
              <>
                <Link
                  to="/login"
                  className="text-[15px] font-medium text-[#9394A1] no-underline transition-colors duration-150 px-4 py-2.5 hover:text-[#EDEDEF]"
                >
                  Login
                </Link>
                <Link
                  to="/register"
                  className="inline-flex items-center justify-center text-[15px] font-semibold text-white bg-[#5E6AD2] px-6 py-2.5 rounded-lg no-underline transition-all duration-150 hover:bg-[#6E7BE3] hover:-translate-y-px"
                >
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
