import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import {
  AlertDialog,
  AlertDialogTrigger,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogCancel,
  AlertDialogAction,
} from './alert-dialog'

describe('AlertDialog primitives', () => {
  it('opens and shows content when the trigger is clicked', () => {
    render(
      <AlertDialog>
        <AlertDialogTrigger asChild>
          <button type="button">Open</button>
        </AlertDialogTrigger>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you sure?</AlertDialogTitle>
            <AlertDialogDescription>This cannot be undone.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction>Confirm</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>,
    )

    fireEvent.click(screen.getByText('Open'))
    expect(screen.getByText('Are you sure?')).toBeInTheDocument()
    expect(screen.getByText('This cannot be undone.')).toBeInTheDocument()
  })

  it('does not render content before opening', () => {
    render(
      <AlertDialog>
        <AlertDialogTrigger asChild>
          <button type="button">Open</button>
        </AlertDialogTrigger>
        <AlertDialogContent>
          <AlertDialogTitle>Hidden</AlertDialogTitle>
        </AlertDialogContent>
      </AlertDialog>,
    )
    expect(screen.queryByText('Hidden')).not.toBeInTheDocument()
  })
})
