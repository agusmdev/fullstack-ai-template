# Demo Page - Design Documentation

## Overview

A bold, neo-brutalist demo page showcasing the full-stack template's capabilities. The design prioritizes impact, memorability, and technical sophistication.

## Aesthetic Direction

**Neo-Brutalist Tech Gallery**
- Raw, unapologetic design with thick borders (3-4px)
- Sharp contrast between dark backgrounds and vibrant accents
- Kinetic energy through staggered animations
- Lime (#a6ff00) and cyan (#00f0ff) accent colors
- Dark concrete base (#0a0a0a, #141414)

## Typography

**Syne** - Display font for headlines and UI
- Bold, geometric, contemporary
- Weights: 400, 600, 700, 800
- Used for all headings and CTA buttons

**JetBrains Mono** - Monospace for terminal
- Clean, modern monospace
- Perfect for code/terminal displays

## Key Features

### 1. Hero Section
- Full-screen grid with animated background
- Staggered text animations (slide-up with cubic-bezier easing)
- Live terminal demo showing Docker startup
- Gradient underline on accent text
- Pulsing "Production Ready" badge

### 2. Features Grid
- 6 feature cards with unique color assignments
- Hover effects: translate + box-shadow in card color
- Animated corner accent that expands on hover
- Staggered entrance animations (100ms delays)

### 3. Tech Stack Section
- Two-column layout (Frontend | Backend)
- Central divider with gradient (lime → cyan)
- Staggered list items with dot indicators
- Hover effects on individual tech items

### 4. CTA Section
- Large, centered call-to-action
- Radial gradient background glow
- Two button styles: primary (filled) and ghost (outline)
- Aggressive hover states with translate + box-shadow

## Animations

All animations use `cubic-bezier(0.34, 1.56, 0.64, 1)` for bounce effects or `ease-out` for fades.

### Key Animation Sequences
1. **Hero Load** (0-1600ms)
   - Badge slide-in (0ms)
   - Title lines (0, 100, 200ms)
   - Subtitle fade (400ms)
   - CTA buttons (600ms)
   - Terminal window (800ms)
   - Terminal lines (1000-1600ms)

2. **Features Grid**
   - Cards appear with 100ms stagger
   - Opacity + translateY animation

3. **Tech List**
   - Items slide in with 50ms stagger
   - Different start delays for Frontend vs Backend

## Color Palette

```css
/* Base */
Background: #0a0a0a
Surface: #141414
Border: #2a2a2a

/* Accents */
Lime: #a6ff00
Cyan: #00f0ff
Purple: #b794f6
Orange: #ffa726
Blue: #42a5f5
Pink: #ff6b9d

/* Text */
Primary: #ffffff
Secondary: rgba(255, 255, 255, 0.7)
Muted: rgba(255, 255, 255, 0.6)
```

## Responsive Behavior

- Hero switches to single column on mobile (<1024px)
- Features grid uses auto-fit with 320px minimum
- Tech stack divider hidden on mobile
- Font sizes scale with clamp() for fluid typography
- All paddings reduce on mobile (4rem → 2rem)

## Technical Highlights

- **Zero dependencies** beyond existing template stack
- Pure CSS animations (no JS animation libraries)
- Google Fonts for distinctive typography
- SVG for custom icons and arrows
- CSS Grid for complex layouts
- Flexbox for component-level layouts

## Usage

Visit `/demo` in your browser to see the page live. No authentication required.

## Customization

To adapt the design:

1. **Colors**: Update CSS custom properties in `demo.css`
2. **Typography**: Change Google Fonts import and font-family declarations
3. **Content**: Modify arrays in `demo.tsx` (features, techStack)
4. **Animations**: Adjust animation-delay values in inline styles

## Design Philosophy

This demo exemplifies:
- **Bold over safe**: Thick borders, saturated colors, aggressive hover states
- **Purposeful animation**: Every motion serves to guide attention
- **Brutalist principles**: Raw, functional, unapologetic
- **Neo-modern fusion**: Contemporary tech aesthetic with timeless brutalism
- **Memorable over pretty**: Design that sticks in memory

The goal wasn't to create something universally appealing, but something impossible to forget.
