---
name: Google Photos Material 3
colors:
  surface: '#f8f9fa'
  surface-dim: '#d9dadb'
  surface-bright: '#f8f9fa'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f3f4f5'
  surface-container: '#edeeef'
  surface-container-high: '#e7e8e9'
  surface-container-highest: '#e1e3e4'
  on-surface: '#191c1d'
  on-surface-variant: '#414754'
  inverse-surface: '#2e3132'
  inverse-on-surface: '#f0f1f2'
  outline: '#727785'
  outline-variant: '#c1c6d6'
  surface-tint: '#005bc0'
  primary: '#005bbf'
  on-primary: '#ffffff'
  primary-container: '#1a73e8'
  on-primary-container: '#ffffff'
  inverse-primary: '#adc7ff'
  secondary: '#b51b15'
  on-secondary: '#ffffff'
  secondary-container: '#d9372b'
  on-secondary-container: '#fffbff'
  tertiary: '#006d2c'
  on-tertiary: '#ffffff'
  tertiary-container: '#008939'
  on-tertiary-container: '#ffffff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d8e2ff'
  primary-fixed-dim: '#adc7ff'
  on-primary-fixed: '#001a41'
  on-primary-fixed-variant: '#004493'
  secondary-fixed: '#ffdad5'
  secondary-fixed-dim: '#ffb4a9'
  on-secondary-fixed: '#410001'
  on-secondary-fixed-variant: '#930004'
  tertiary-fixed: '#89fa9b'
  tertiary-fixed-dim: '#6ddd81'
  on-tertiary-fixed: '#002108'
  on-tertiary-fixed-variant: '#005320'
  background: '#f8f9fa'
  on-background: '#191c1d'
  surface-variant: '#e1e3e4'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 57px
    fontWeight: '400'
    lineHeight: 64px
    letterSpacing: -0.25px
  display-md:
    fontFamily: Inter
    fontSize: 45px
    fontWeight: '400'
    lineHeight: 52px
  display-sm:
    fontFamily: Inter
    fontSize: 36px
    fontWeight: '400'
    lineHeight: 44px
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '400'
    lineHeight: 40px
  headline-md:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '400'
    lineHeight: 36px
  headline-sm:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '400'
    lineHeight: 32px
  title-lg:
    fontFamily: Inter
    fontSize: 22px
    fontWeight: '500'
    lineHeight: 28px
  title-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '500'
    lineHeight: 24px
    letterSpacing: 0.15px
  title-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: 0.1px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
    letterSpacing: 0.5px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
    letterSpacing: 0.25px
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
  label-lg:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: 0.1px
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.5px
  label-sm:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 16px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1rem
  margin: 1.5rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2rem
---

## Brand & Style

This design system merges the accessible foundations of Material 3 with modern glassmorphism and the vibrant identity of Google AI. The aesthetic is centered around luminous clarity, immersive imagery, and intelligent utility.

- **Target Audience:** Everyday consumers, photography enthusiasts, and memory-keepers seeking an intuitive, emotionally resonant archive of their lives.
- **Emotional Response:** Inspiring, nostalgic, weightless, and cutting-edge. The interface should feel like looking through clean glass at treasured memories, enhanced by ambient intelligence.
- **Design Style:** A hybrid of **Glassmorphism** and **Corporate / Modern (Material 3)**. Translucent surfaces, vibrant background blurs, and signature Google AI multi-color gradients provide a sense of depth and computational intelligence without sacrificing readability or utility.

## Colors

The color architecture is built to support pristine light mode and deep OLED dark mode (`#000000`), utilizing dynamic tonal surfaces and the iconic Google AI multi-color gradient (Blue `#1a73e8`, Red `#ea4335`, Yellow `#fbbc04`, Green `#34a853`, and Purple `#9333ea`) as an accent system for AI-powered features, search highlights, and active states.

- **Surface Tiers:** Surfaces use semi-transparent white in light mode (`rgba(255, 255, 255, 0.85)`) and deep OLED black with subtle luminance in dark mode (`rgba(18, 18, 18, 0.85)`) to support frosted glass effects.
- **Semantic Mapping:** High-contrast text guarantees WCAG AAA compliance against shifting photographic backdrops.

## Typography

Using Inter as a geometric, highly legible stand-in for Google Sans, the typography scale relies on optical sizing weights (400 regular for body, 500 medium for titles and labels) to maintain clarity over complex photographic backgrounds. 

- **Scale Adaptations:** Display sizes scale down fluidly on viewports under 600px to prevent awkward wraps in memory headers and album titles.

## Layout & Spacing

The layout employs a fluid grid system optimized for dense, edge-to-edge media consumption. 

- **Grid System:** A responsive 12-column grid on desktop, scaling down to a 4-column layout on mobile devices. 
- **Gutters & Margins:** Uses tight 4px–8px gutters between grid items (photos/albums) to maximize visual real estate, paired with generous 16px–24px outer margins.
- **Breakpoints:** Mobile (< 600px), Tablet (600px – 1024px), and Desktop (> 1024px). Spacing scales dynamically to balance touch targets on mobile with information density on desktop.

## Elevation & Depth

Depth is primarily achieved through **Glassmorphism** and layered translucency rather than traditional heavy drop shadows.

- **Backdrop Blurs:** Floating navigation bars, search overlays, and bottom sheets use heavy backdrop blurring (`blur(16px)` to `blur(24px)`) paired with semi-transparent surface fills.
- **Ambient Shadows:** Minimalist, diffused, and color-tinted shadows lift interactive elements slightly off the canvas, establishing clear focal points without distracting from underlying photography.

## Shapes

The shape language relies heavily on friendly, organic roundedness (Level 2 roundedness scale).

- **Containers & Cards:** Core image containers, floating action buttons, and modal dialogs feature generous radii (`1rem` to `1.5rem` / `rounded-lg` / `rounded-xl`). Pill shapes (`3`) are reserved for filter chips, search tags, and AI assistant triggers.

## Components

- **Buttons:** Filled buttons feature pill-shaped geometries with optional Google AI multi-color gradient borders or fills. Text and outlined variants rely on low-contrast ghost borders and translucent hover states.
- **Chips:** Filter and suggestion chips use rounded pill shapes, displaying subtle backdrop blur and shifting to active states highlighted by the multi-color AI accent spectrum.
- **Lists:** Dense, borderless list rows with generous touch targets (min 48px), featuring subtle hover highlights and clear typographic hierarchy for metadata like dates and locations.
- **Checkboxes & Radio Buttons:** Custom M3 check-mark animations with smooth state transitions, utilizing primary brand blue for selection states.
- **Input Fields:** Search and input fields utilize fully rounded pill containers with frosted glass backgrounds, embedded trailing AI Sparkle icons, and clear placeholder text.
- **Cards:** Edge-to-edge media cards with rounded corners (`1rem`), incorporating soft zoom hover micro-interactions and overlaid glassmorphic metadata badges.
- **Additional Components:** Floating Action Buttons (FABs) with dynamic multi-color AI gradients; Memory carousels with smooth horizontal snap-scroll physics; Bottom sheets with frosted glass drag-handles for sharing and editing tools.