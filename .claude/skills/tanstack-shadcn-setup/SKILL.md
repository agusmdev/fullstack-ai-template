---
name: tanstack-shadcn-setup
description: Configure Tailwind CSS v4 and shadcn/ui with theming, dark mode, and CSS variables. SHARED skill for both TanStack Start (SSR) and TanStack Router (SPA).
---

# TanStack shadcn/ui Setup

## Overview

This skill covers setting up Tailwind CSS v4 and shadcn/ui in TanStack Start or TanStack Router projects. shadcn/ui is a collection of re-usable components built with Radix UI and Tailwind CSS that you copy into your project.

**Important:** This skill works for both:
- TanStack Start (SSR full-stack)
- TanStack Router (SPA client-only)

## Prerequisites

- Existing TanStack Start or TanStack Router project
- Bun or npm package manager
- Node.js 18+

## Step 1: Install Tailwind CSS v4

Install Tailwind CSS v4 and its dependencies:

```bash
bun add -D tailwindcss@next @tailwindcss/postcss@next postcss autoprefixer
```

Or with npm:

```bash
npm install -D tailwindcss@next @tailwindcss/postcss@next postcss autoprefixer
```

## Step 2: Initialize Tailwind Configuration

Create `postcss.config.js` in the project root:

```javascript
export default {
  plugins: {
    '@tailwindcss/postcss': {},
    autoprefixer: {},
  },
}
```

## Step 3: Create Global CSS File

Create `src/app.css` (or `src/index.css`) with Tailwind directives and CSS variables:

```css
@import "tailwindcss";

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
    --popover: 0 0% 100%;
    --popover-foreground: 222.2 84% 4.9%;
    --primary: 222.2 47.4% 11.2%;
    --primary-foreground: 210 40% 98%;
    --secondary: 210 40% 96.1%;
    --secondary-foreground: 222.2 47.4% 11.2%;
    --muted: 210 40% 96.1%;
    --muted-foreground: 215.4 16.3% 46.9%;
    --accent: 210 40% 96.1%;
    --accent-foreground: 222.2 47.4% 11.2%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;
    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: 222.2 84% 4.9%;
    --radius: 0.5rem;
    --chart-1: 12 76% 61%;
    --chart-2: 173 58% 39%;
    --chart-3: 197 37% 24%;
    --chart-4: 43 74% 66%;
    --chart-5: 27 87% 67%;
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    --card: 222.2 84% 4.9%;
    --card-foreground: 210 40% 98%;
    --popover: 222.2 84% 4.9%;
    --popover-foreground: 210 40% 98%;
    --primary: 210 40% 98%;
    --primary-foreground: 222.2 47.4% 11.2%;
    --secondary: 217.2 32.6% 17.5%;
    --secondary-foreground: 210 40% 98%;
    --muted: 217.2 32.6% 17.5%;
    --muted-foreground: 215 20.2% 65.1%;
    --accent: 217.2 32.6% 17.5%;
    --accent-foreground: 210 40% 98%;
    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 210 40% 98%;
    --border: 217.2 32.6% 17.5%;
    --input: 217.2 32.6% 17.5%;
    --ring: 212.7 26.8% 83.9%;
    --chart-1: 220 70% 50%;
    --chart-2: 160 60% 45%;
    --chart-3: 30 80% 55%;
    --chart-4: 280 65% 60%;
    --chart-5: 340 75% 55%;
  }
}

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground;
  }
}
```

## Step 4: Import CSS in Root Route

For TanStack Start, update `src/routes/__root.tsx`:

```tsx
import { createRootRoute, Outlet } from '@tanstack/react-router'
import { Meta, Scripts } from '@tanstack/react-start'
import '../app.css'

export const Route = createRootRoute({
  head: () => ({
    meta: [
      { charSet: 'utf-8' },
      { name: 'viewport', content: 'width=device-width, initial-scale=1' },
    ],
  }),
  component: () => (
    <html>
      <head>
        <Meta />
      </head>
      <body>
        <Outlet />
        <Scripts />
      </body>
    </html>
  ),
})
```

For TanStack Router (SPA), update your entry point (usually `src/main.tsx`):

```tsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import { RouterProvider, createRouter } from '@tanstack/react-router'
import { routeTree } from './routeTree.gen'
import './app.css'

const router = createRouter({ routeTree })

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}

const rootElement = document.getElementById('root')!
if (!rootElement.innerHTML) {
  const root = ReactDOM.createRoot(rootElement)
  root.render(
    <React.StrictMode>
      <RouterProvider router={router} />
    </React.StrictMode>
  )
}
```

## Step 5: Install shadcn/ui CLI

Install shadcn/ui CLI globally:

```bash
bun add -g shadcn
```

Or use npx without installing:

```bash
bunx shadcn@latest
```

## Step 6: Initialize shadcn/ui

Run the init command to set up shadcn/ui:

```bash
bunx shadcn@latest init
```

The CLI will ask you a few questions:

1. **Would you like to use TypeScript?** → Yes
2. **Which style would you like to use?** → New York or Default
3. **Which color would you like to use as base color?** → Slate (or your preference)
4. **Where is your global CSS file?** → `src/app.css` (or `src/index.css`)
5. **Would you like to use CSS variables for colors?** → Yes
6. **Where is your tailwind.config.js located?** → Press enter (auto-detected)
7. **Configure the import alias for components?** → `~/components`
8. **Configure the import alias for utils?** → `~/lib/utils`
9. **Are you using React Server Components?** → No (for TanStack Start) or No (for TanStack Router)

This creates:
- `components.json` - shadcn/ui configuration
- `src/lib/utils.ts` - Utility functions
- `src/components/ui/` - Component directory (initially empty)

## Step 7: Update tsconfig.json Paths

Ensure `tsconfig.json` has the correct path aliases:

```json
{
  "compilerOptions": {
    "jsx": "react-jsx",
    "moduleResolution": "Bundler",
    "module": "ESNext",
    "target": "ES2022",
    "skipLibCheck": true,
    "strictNullChecks": true,
    "baseUrl": ".",
    "paths": {
      "~/*": ["./src/*"]
    }
  }
}
```

## Step 8: Verify components.json

Check that `components.json` was created with correct settings:

```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "new-york",
  "rsc": false,
  "tsx": true,
  "tailwind": {
    "config": "tailwind.config.js",
    "css": "src/app.css",
    "baseColor": "slate",
    "cssVariables": true
  },
  "aliases": {
    "components": "~/components",
    "utils": "~/lib/utils"
  }
}
```

## Step 9: Install Your First Component

Test the setup by installing a component:

```bash
bunx shadcn@latest add button
```

This creates `src/components/ui/button.tsx`.

## Step 10: Add Dark Mode Support (Optional)

Install next-themes for dark mode:

```bash
bun add next-themes
```

Create a theme provider `src/components/theme-provider.tsx`:

```tsx
import { createContext, useContext, useEffect, useState } from 'react'

type Theme = 'dark' | 'light' | 'system'

type ThemeProviderProps = {
  children: React.ReactNode
  defaultTheme?: Theme
  storageKey?: string
}

type ThemeProviderState = {
  theme: Theme
  setTheme: (theme: Theme) => void
}

const ThemeProviderContext = createContext<ThemeProviderState | undefined>(undefined)

export function ThemeProvider({
  children,
  defaultTheme = 'system',
  storageKey = 'ui-theme',
  ...props
}: ThemeProviderProps) {
  const [theme, setTheme] = useState<Theme>(
    () => (localStorage.getItem(storageKey) as Theme) || defaultTheme
  )

  useEffect(() => {
    const root = window.document.documentElement
    root.classList.remove('light', 'dark')

    if (theme === 'system') {
      const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches
        ? 'dark'
        : 'light'
      root.classList.add(systemTheme)
      return
    }

    root.classList.add(theme)
  }, [theme])

  const value = {
    theme,
    setTheme: (theme: Theme) => {
      localStorage.setItem(storageKey, theme)
      setTheme(theme)
    },
  }

  return (
    <ThemeProviderContext.Provider {...props} value={value}>
      {children}
    </ThemeProviderContext.Provider>
  )
}

export const useTheme = () => {
  const context = useContext(ThemeProviderContext)
  if (context === undefined) throw new Error('useTheme must be used within a ThemeProvider')
  return context
}
```

Wrap your app with ThemeProvider in `__root.tsx`:

```tsx
import { createRootRoute, Outlet } from '@tanstack/react-router'
import { Meta, Scripts } from '@tanstack/react-start'
import { ThemeProvider } from '~/components/theme-provider'
import '../app.css'

export const Route = createRootRoute({
  component: () => (
    <html suppressHydrationWarning>
      <head>
        <Meta />
      </head>
      <body>
        <ThemeProvider defaultTheme="system" storageKey="ui-theme">
          <Outlet />
        </ThemeProvider>
        <Scripts />
      </body>
    </html>
  ),
})
```

## Step 11: Create a Theme Toggle Component

```bash
bunx shadcn@latest add dropdown-menu
```

Create `src/components/theme-toggle.tsx`:

```tsx
import { Moon, Sun } from 'lucide-react'
import { Button } from '~/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '~/components/ui/dropdown-menu'
import { useTheme } from '~/components/theme-provider'

export function ThemeToggle() {
  const { setTheme } = useTheme()

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="icon">
          <Sun className="h-[1.2rem] w-[1.2rem] rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
          <Moon className="absolute h-[1.2rem] w-[1.2rem] rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
          <span className="sr-only">Toggle theme</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem onClick={() => setTheme('light')}>Light</DropdownMenuItem>
        <DropdownMenuItem onClick={() => setTheme('dark')}>Dark</DropdownMenuItem>
        <DropdownMenuItem onClick={() => setTheme('system')}>System</DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
```

## Verification

After setup, verify:

1. **Tailwind works:** Create a test component with Tailwind classes
2. **CSS variables work:** Check that colors use `hsl(var(--primary))`
3. **shadcn/ui components work:** Add and use a Button component
4. **Dark mode works:** Toggle between light/dark themes
5. **Dev server runs:** `bun run dev` starts without errors

Example test component:

```tsx
import { Button } from '~/components/ui/button'

export default function TestPage() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="space-y-4">
        <h1 className="text-4xl font-bold">Tailwind & shadcn/ui Test</h1>
        <Button>Click me</Button>
        <Button variant="secondary">Secondary</Button>
        <Button variant="outline">Outline</Button>
      </div>
    </div>
  )
}
```

## Common Issues

### Issue: Tailwind styles not applying

**Solution:** Ensure `app.css` is imported in your root route or entry point.

### Issue: Components not found

**Solution:** Check `tsconfig.json` paths match `components.json` aliases.

### Issue: Dark mode not working

**Solution:** Add `suppressHydrationWarning` to `<html>` tag in `__root.tsx`.

### Issue: CSS variables not resolving

**Solution:** Verify `@import "tailwindcss"` is at the top of `app.css`.

## Component Installation

After setup, install components as needed:

```bash
# Common components
bunx shadcn@latest add button
bunx shadcn@latest add input
bunx shadcn@latest add card
bunx shadcn@latest add form
bunx shadcn@latest add dialog
bunx shadcn@latest add dropdown-menu
bunx shadcn@latest add table
bunx shadcn@latest add toast

# Install all at once
bunx shadcn@latest add button input card form dialog dropdown-menu table toast
```

## Project Structure After Setup

```
your-project/
├── src/
│   ├── routes/                 # TanStack routes
│   ├── components/
│   │   ├── ui/                 # shadcn/ui components
│   │   │   ├── button.tsx
│   │   │   └── ...
│   │   ├── theme-provider.tsx  # Dark mode provider
│   │   └── theme-toggle.tsx    # Theme toggle component
│   ├── lib/
│   │   └── utils.ts            # Utility functions (cn, etc.)
│   ├── app.css                 # Global styles + Tailwind
│   └── router.tsx              # Router config
├── components.json             # shadcn/ui config
├── postcss.config.js           # PostCSS config
├── tsconfig.json               # TypeScript config
└── vite.config.ts              # Vite config
```

## Notes

- shadcn/ui components are copied into your project, not installed as a package
- You own the code and can customize components freely
- Tailwind v4 uses `@import "tailwindcss"` instead of `@tailwind` directives
- CSS variables enable dynamic theming without JavaScript
- Dark mode is implemented with CSS classes (`.dark`)
- Works identically in both TanStack Start (SSR) and TanStack Router (SPA)

## Next Steps

After setup:
- Install specific components you need
- Customize theme colors in `app.css`
- Create reusable component compositions
- Set up form handling with react-hook-form (see `tanstack-shadcn-forms` skill)
- Build data tables (see `tanstack-shadcn-data-tables` skill)

## Resources

- [Tailwind CSS v4 Documentation](https://tailwindcss.com/docs)
- [shadcn/ui Documentation](https://ui.shadcn.com)
- [Radix UI Primitives](https://www.radix-ui.com/primitives)
- [TanStack Start Documentation](https://tanstack.com/start)
- [TanStack Router Documentation](https://tanstack.com/router)
