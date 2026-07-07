# Synthex Logo — Specifications & Usage Guide

> Version 1.0 | July 2026  
> Part of the Linux Synthex Brand Identity Guidelines

---

## 1. Logo Architecture

The Synthex brand mark consists of three distinct elements:

```
┌─────────────────────────────────────────────────┐
│                     Icon Mark                    │
│        Stylised sun/gear/hexagon hybrid          │
├─────────────────────────────────────────────────┤
│                   Wordmark                       │
│     "Synthex" — custom lettering, Inter-based      │
├─────────────────────────────────────────────────┤
│                   Lockup                         │
│     Icon Mark + Wordmark in fixed relationship    │
└─────────────────────────────────────────────────┘
```

---

## 2. SVG Files

| File              | Description                     | Dimensions | Use Case                  |
|-------------------|---------------------------------|------------|---------------------------|
| `synthex-logo.svg`  | Full lockup (icon + wordmark)   | 256×64     | Website header, docs      |
| `synthex-icon.svg`  | Icon mark only                  | 128×128    | Favicon, app icon, avatar |

---

## 3. Icon Mark — Construction Grid

The icon mark is constructed on a **24×24 unit grid** with a **32×32 artboard** and **2-unit padding** on all sides.

```
         Top padding: 2u
             │
    ┌────────┴────────┐
    │                 │
    │    ╱▔▔╲         │  ── Outer gear ring
    │   ╱    ╲        │     Radius: 12u (outer)
    │  │  ╱╲  │       │     Teeth: 8
    │  │ │  │ │       │
    │  │ ╲╱  │       │  ── Inner hexagon
    │  ╲    ╱        │     Radius: 5u
    │   ╲▁▁╱         │
    │  ┌────┐        │  ── Open circle centre
    │  │ ○  │        │     Radius: 2u
    │  └────┘        │
    └────────────────┘
             │
      Bottom padding: 2u
```

### 3.1 Geometry Breakdown

| Element          | Description                                    | SVG Technique              |
|------------------|------------------------------------------------|----------------------------|
| Sun rays (8)     | Radiating from centre, 45° intervals           | `<polygon>` or `<path>`    |
| Gear teeth (8)   | Notches around outer ring, offset from rays    | `<path>` with arc commands |
| Outer ring        | Circle connecting gear teeth                   | `<circle>` with `stroke`   |
| Inner hexagon    | Regular hexagon, rotated 90°                   | `<polygon>`                |
| Centre circle    | Cutout showing open-source nature              | `<circle>` with `mask`     |

### 3.2 Colour — Full Colour Logo

| Element        | Fill/Stroke       | Hex       |
|----------------|-------------------|-----------|
| Sun rays       | Synthex Amber       | `#FFB300` |
| Gear ring      | Synthex Amber       | `#FFB300` |
| Gear teeth     | Synthex Amber (dark)| `#E6A000` |
| Inner hexagon  | Synthex Deep Blue   | `#1565C0` |
| Centre circle  | Transparent (cutout)| —        |
| Wordmark       | White              | `#FFFFFF` |

### 3.3 Colour — Monochrome Logo

| Variant  | Fill/Stroke     | Usage                        |
|----------|-----------------|------------------------------|
| Light    | `#FFFFFF`       | On dark backgrounds          |
| Dark     | `#1A1A2E`       | On light backgrounds         |
| Grey     | `#616161`       | Muted / disabled contexts    |

---

## 4. Wordmark Specifications

### 4.1 Typography
The wordmark "Synthex" uses **Inter Bold** with custom letter-spacing adjustments:

| Character | Tracking  | Notes                        |
|-----------|-----------|------------------------------|
| S         | +20       | Slightly wider for presence  |
| o         | +15       | Standard round glyph         |
| l         | +15       | Narrow glyph, tracking helps |
| u         | +15       |                              |
| s         | +10       | Final letter, tightened      |

### 4.2 Wordmark Colour
- **Full colour**: White (`#FFFFFF`) — always on brand backgrounds
- **Dark background**: White (`#FFFFFF`)
- **Light background**: Synthex Deep Blue (`#1565C0`)

---

## 5. Lockup Geometry

The lockup places the icon mark to the left of the wordmark with fixed spacing:

```
[Icon Mark]  [spacer: 8u]  [Wordmark: "Synthex"]
```

- **Alignment**: Vertical centre alignment between icon and wordmark
- **Spacer**: 8 units of clear space (1/3 of icon width)
- **Height relationship**: Wordmark cap height = 80% of icon mark height

### 5.1 Lockup Variants

| Variant     | Layout               | Dimensions    | Use                         |
|-------------|----------------------|---------------|-----------------------------|
| Horizontal  | Icon + Wordmark side | 256×64        | Primary, most uses          |
| Stacked     | Icon above Wordmark  | 128×96        | Square spaces, app icons    |
| Icon-only   | Mark only            | 128×128       | Small spaces, app icons     |

---

## 6. Usage Guidelines

### 6.1 Clear Space
Minimum clear space = **the height of the uppercase "S"** in the wordmark on all sides.

```
┌─────────────────────────────────────────────┐
│                 Clear Space                  │
│    ┌─────────────────────────────────┐       │
│    │         SYNTHEX LOGO              │       │
│    └─────────────────────────────────┘       │
│                 Clear Space                  │
└─────────────────────────────────────────────┘
```

### 6.2 Minimum Sizes

| Variant     | Digital | Print    |
|-------------|---------|----------|
| Horizontal  | 64px w  | 0.5 in   |
| Stacked     | 48px w  | 0.4 in   |
| Icon-only   | 24px    | 0.2 in   |

### 6.3 Background Contrast Requirements

| Background              | Logo Variant         |
|-------------------------|----------------------|
| Dark (#1A1A2E or darker)| Full colour (white) |
| Light (#FAFAFA or lighter)| Full colour with Deep Blue wordmark |
| Photo (dark area)       | Full colour          |
| Photo (light area)      | Monochrome light     |
| Brand gradient          | Full colour (white)  |
| Any busy background     | Monochrome (white)   |

---

## 7. Prohibited Uses

```
✓ DO: Use provided SVG files directly
✓ DO: Scale proportionally (lock aspect ratio)
✓ DO: Use approved colour variants
✗ DON'T: Stretch or distort
✗ DON'T: Change colours outside palette
✗ DON'T: Add outlines, shadows, or glow effects
✗ DON'T: Rotate the icon mark
✗ DON'T: Recreate the wordmark in a different font
✗ DON'T: Place on low-contrast backgrounds
✗ DON'T: Rearrange lockup elements
✗ DON'T: Use the icon mark as a patterned background
```

---

## 8. File Formats

| Format | Use                   | Notes                         |
|--------|-----------------------|-------------------------------|
| SVG    | Web, scaling          | Preferred source format       |
| PNG    | Legacy, print preview | @1x, @2x, @3x provided        |
| ICO    | Windows favicon       | 32×32, 16×16 included         |
| ICNS   | macOS icon            | All sizes embedded            |

---

## 9. Source Files

All logo source files are maintained in this directory:

```
logo/
├── synthex-logo.svg          # Full lockup (horizontal)
├── synthex-logo-stacked.svg  # Stacked lockup
├── synthex-icon.svg          # Icon mark only
├── synthex-icon-mono-light.svg  # Monochrome (light)
├── synthex-icon-mono-dark.svg   # Monochrome (dark)
└── logo-specs.md           # This document
```

---

*© 2026 Linux Synthex Project. Synthex and the Synthex logo are trademarks of the Linux Synthex Project.*
