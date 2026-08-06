import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ThemeToggle } from './ThemeToggle'
import { THEME_STORAGE_KEY } from '@/lib/theme'

describe('ThemeToggle', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.classList.remove('dark')
  })
  afterEach(() => vi.restoreAllMocks())

  it('renders a toggle button with an accessible label', () => {
    render(<ThemeToggle />)
    expect(screen.getByLabelText('Toggle theme')).toBeInTheDocument()
  })

  it('opens a menu with Light / Dark / System options on click', () => {
    render(<ThemeToggle />)
    fireEvent.click(screen.getByLabelText('Toggle theme'))
    expect(screen.getByText('Light')).toBeInTheDocument()
    expect(screen.getByText('Dark')).toBeInTheDocument()
    expect(screen.getByText('System')).toBeInTheDocument()
  })

  it('applies dark theme and persists to localStorage when Dark is selected', () => {
    render(<ThemeToggle />)
    fireEvent.click(screen.getByLabelText('Toggle theme'))
    fireEvent.click(screen.getByText('Dark'))
    expect(document.documentElement.classList.contains('dark')).toBe(true)
    expect(localStorage.getItem(THEME_STORAGE_KEY)).toBe('dark')
  })

  it('applies light theme and persists when Light is selected', () => {
    document.documentElement.classList.add('dark')
    render(<ThemeToggle />)
    fireEvent.click(screen.getByLabelText('Toggle theme'))
    fireEvent.click(screen.getByText('Light'))
    expect(document.documentElement.classList.contains('dark')).toBe(false)
    expect(localStorage.getItem(THEME_STORAGE_KEY)).toBe('light')
  })

  it('reflects the stored theme as active on mount', () => {
    localStorage.setItem(THEME_STORAGE_KEY, 'dark')
    render(<ThemeToggle />)
    fireEvent.click(screen.getByLabelText('Toggle theme'))
    const darkItem = screen.getByText('Dark').closest('[role="menuitemradio"]')
    expect(darkItem).toHaveAttribute('aria-checked', 'true')
  })
})
