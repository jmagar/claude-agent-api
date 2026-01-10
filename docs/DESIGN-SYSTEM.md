# Design System: Claude Agent Web Interface

**Extracted from**: Interactive wireframes (18 HTML files)
**Date**: 2026-01-10
**Status**: Production-ready

This document captures all visual design decisions from the wireframes to ensure pixel-perfect implementation.

---

## Color Palette

### Light Mode (Default)

**Backgrounds**
- Primary: `#ffffff` (white) - Main content areas
- Secondary: `#f5f5f5` - Cards, message bubbles
- Tertiary: `#fafafa` - Sidebar, subtle backgrounds
- Disabled: `#e5e5e5` - Disabled states, placeholders

**Text**
- Primary: `#333333` - Main text
- Secondary: `#666666` - Labels, metadata
- Tertiary: `#999999` - Placeholder text

**Borders**
- Primary: `#dddddd` - Standard borders
- Secondary: `#cccccc` - Emphasized borders
- Tertiary: `#f0f0f0` - Subtle dividers

**Semantic Colors**
- **User Messages**: `#e8f4ff` (bg), `#b3d9ff` (border)
- **Assistant Messages**: `#f5f5f5` (bg)
- **Success**: `#d4edda` (bg), `#155724` (text)
- **Warning**: `#fff3cd` (bg), `#ffc107` (border), `#856404` (text)
- **Error**: `#f8d7da` (bg), `#dc3545` (border), `#721c24` (text)
- **Approval Card**: `#fffbf0` (bg - light orange)
- **Error Card**: `#fff5f5` (bg - very light red)

### Dark Mode

**Backgrounds**
- Primary: `#0d0d0d` - Pure dark
- Secondary: `#1a1a1a` - Dark gray
- Tertiary: `#2a2a2a` - Medium dark

**Text**
- Primary: `#e0e0e0` - Light text
- Secondary: `#999999`
- Tertiary: `#666666`

**Semantic Colors (Dark)**
- User Messages: `#1e3a5f` (dark blue)
- Success: `#1e4d2b` (dark green), `#7dff9f` (neon green text)
- Code/Syntax: `#7dff9f` (neon green)

---

## Typography

### Font Family
```css
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
```

### Type Scale

| Size | Usage | Weight | Line Height |
|------|-------|--------|-------------|
| 18px | Section headers | 600 | 1.4 |
| 16px | Page titles, headings | 600 | 1.5 |
| 14px | Body text, UI elements | 400-500 | 1.5 |
| 13px | Sidebar items, labels | 400-500 | 1.5 |
| 12px | Secondary text, metadata | 400 | 1.4 |
| 11px | Uppercase labels, badges | 600 | 1.4 |
| 10px | Small badges | 600 | 1.4 |

### Font Weights
- Regular: 400
- Medium: 500
- Semibold: 600
- Bold: 700

---

## Spacing Scale

All spacing follows 4px base unit:

| Value | Usage |
|-------|-------|
| 2px | Micro spacing, inline gaps |
| 4px | Extra small padding |
| 6px | Small padding, badge spacing |
| 8px | Base unit, common gaps |
| 12px | Medium padding, card padding |
| 16px | Large padding, section padding |
| 20px | Container padding, message gaps |
| 24px | Section margins, modal spacing |
| 40px | Mega spacing, large containers |

---

## Border Radius

| Value | Usage |
|-------|-------|
| 3px | Small badges, pills |
| 4px | Small buttons, inputs |
| 6px | Standard buttons, cards |
| 8px | Larger cards, sections |
| 12px | Modal dialogs |
| 18px | Mobile inputs, rounded elements |
| 20px | Pill-shaped buttons |
| 24px | Mobile device frames |
| 50% | Perfect circles (avatars, toggles) |

---

## Shadows

```css
/* Card/Autocomplete shadow */
box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);

/* Modal shadow */
box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);

/* Mobile sidebar shadow */
box-shadow: 2px 0 8px rgba(0, 0, 0, 0.15);
```

---

## Component Specifications

### Buttons

**Standard Button**
- Height: 40px
- Padding: 8px 16px
- Font size: 14px
- Border radius: 6px
- Font weight: 500

**Compact Button**
- Height: 36px
- Padding: 8px 12px
- Font size: 13px

**Icon Button**
- Size: 32px × 32px (desktop)
- Size: 28px × 28px (mobile)
- Border radius: 4px

**Button Variants**
- Primary: `#333` background, white text
- Success: `#28a745` background
- Danger: `#dc3545` background
- Secondary: White background, border, `#333` text

### Input Fields

**Text Input**
- Height: 40px
- Padding: 10px 12px
- Font size: 14px
- Border: 1px solid #ddd
- Border radius: 6px

**Textarea**
- Min height: 40px
- Max height: 80px (mobile)
- Border radius: 6px (desktop), 18px (mobile)
- Padding: 8-12px
- Resize: vertical

### Message Bubbles

- Padding: 12px 16px
- Border radius: 8px
- Border: 1px solid #ddd
- Max width: 70% of container

### Cards

- Padding: 12-16px
- Border radius: 6-8px
- Border: 1px solid #ddd
- Gap between cards: 6-12px

### Tool Cards

**Standard**
- Padding: 12-16px
- Border: 1px solid #ccc
- Background: white
- Border radius: 6-8px

**Approval State**
- Border: 2px solid #ffc107
- Background: #fffbf0

**Error State**
- Border: 2px solid #dc3545
- Background: #fff5f5

### Modals

- Max width: 600px (tool management), 640px (command palette)
- Border radius: 12px
- Shadow: 0 20px 60px rgba(0, 0, 0, 0.3)
- Header padding: 20px 24px
- Content padding: 16-24px
- Footer padding: 16px 24px

### Toggle Switches

- Dimensions: 44px × 24px
- Toggle circle: 20px diameter
- Inset: 2px from edge
- Border radius: 12px (switch), 50% (circle)
- Colors: #333 (on), #ccc (off)

---

## Layout Patterns

### Desktop Layout

**Container**
- Max width: 1400px
- Padding: 20px

**Sidebar**
- Width: 280px
- Background: #fafafa
- Border right: 2px solid #ddd

**Main Content**
- Flex: 1 (remaining width)
- Background: white

**Header**
- Padding: 16px 20px
- Border bottom: 1px solid #ddd

**Chat Area**
- Padding: 20px
- Overflow: auto

### Mobile Layout

**Frame**
- Width: 320px (minimum)
- Height: 600px

**Header**
- Padding: 12px
- Compact icons: 28px

**Content**
- Padding: 12px

**Bottom Navigation**
- Fixed position
- Height: 56px
- 4 tabs: Chat, Search, Settings, New

---

## Interactive States

### Buttons
- Default: Solid background
- Hover: Lighter/darker shade
- Active: Bold emphasis
- Disabled: Gray, no pointer events

### List Items
- Default: Normal
- Hover: `background: #f5f5f5`
- Selected: `background: #f5f5f5` + `border-left: 3px solid #333`

### Form Inputs
- Default: `1px solid #ddd`
- Focus: Darker border (implied)
- Placeholder: `#999` color

### Toggle Switches
- On: `#333` background, toggle right
- Off: `#ccc` background, toggle left

---

## Animations

### Loading States

```css
/* Skeleton shimmer */
background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
background-size: 200% 100%;
animation: loading 1.5s ease-in-out infinite;

@keyframes loading {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
```

### Spinner

```css
animation: spin 1s linear infinite;

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
```

### Cursor Blink

```css
animation: blink 1s infinite;

@keyframes blink {
  50% { opacity: 0; }
}
```

---

## Responsive Breakpoints

```css
/* Mobile */
@media (max-width: 767px) {
  /* Hamburger menu */
  /* Bottom navigation */
  /* Full-screen composer */
}

/* Tablet */
@media (min-width: 768px) and (max-width: 1023px) {
  /* Collapsible sidebar */
}

/* Desktop */
@media (min-width: 1024px) {
  /* Fixed sidebar */
  /* Multi-column layouts */
}
```

### Mobile Adaptations
- Sidebar: Overlay with hamburger toggle
- Navigation: Fixed bottom bar (4 tabs)
- Touch targets: Minimum 44px
- Font sizes: Slightly reduced
- Inputs: Full-width, rounded edges

---

## Accessibility

### Color Contrast
- All text meets WCAG AA standards
- Primary text (#333) on white: 12.6:1
- Secondary text (#666) on white: 5.7:1

### Touch Targets
- Minimum: 44px × 44px (iOS/Android guidelines)
- Mobile buttons: 36-44px height

### Focus States
- Visible focus indicators on all interactive elements
- Keyboard navigation support

---

## Design Tokens (Tailwind Format)

```javascript
module.exports = {
  colors: {
    gray: {
      50: '#fafafa',
      100: '#f5f5f5',
      200: '#e5e5e5',
      300: '#dddddd',
      400: '#cccccc',
      500: '#999999',
      600: '#666666',
      700: '#333333',
      900: '#0d0d0d',
    },
    blue: {
      light: '#e8f4ff',
      border: '#b3d9ff',
      dark: '#1e3a5f',
    },
    green: {
      light: '#d4edda',
      DEFAULT: '#28a745',
      dark: '#155724',
      neon: '#7dff9f',
    },
    yellow: {
      light: '#fffbf0',
      bg: '#fff3cd',
      border: '#ffc107',
      text: '#856404',
    },
    red: {
      light: '#f8d7da',
      bg: '#fff5f5',
      DEFAULT: '#dc3545',
      dark: '#721c24',
    },
  },
  spacing: {
    // ... extends default 0-16
    20: '20px',
    24: '24px',
    40: '40px',
  },
  borderRadius: {
    3: '3px',
    6: '6px',
    8: '8px',
    12: '12px',
    18: '18px',
    20: '20px',
    24: '24px',
  },
  fontSize: {
    10: '10px',
    11: '11px',
    12: '12px',
    13: '13px',
    14: '14px',
    16: '16px',
    18: '18px',
  },
}
```

---

## Component Library Inventory

From wireframes, we need these components:

### Core Components (P1 - MVP)
- [ ] Button (primary, secondary, danger, icon)
- [ ] Input (text, textarea, search)
- [ ] Message bubble (user, assistant)
- [ ] MessageList (virtualized)
- [ ] Composer (with Shift+Enter)
- [ ] Sidebar
- [ ] SessionList
- [ ] SessionItem
- [ ] ModeToggle (Brainstorm/Code)
- [ ] ToolCallCard
- [ ] ChatHeader
- [ ] IconButton

### Extended Components (P2)
- [ ] Modal (base, tool management)
- [ ] AutocompleteMenu (@/ slash commands)
- [ ] ToolApprovalCard
- [ ] StatusBadge
- [ ] ToggleSwitch
- [ ] Dropdown/Select
- [ ] LoadingSkeleton
- [ ] EmptyState

### Advanced Components (P3)
- [ ] CommandPalette (Cmd+K)
- [ ] PlateJS Editor (artifacts)
- [ ] SettingsPanel
- [ ] MCPServerCard
- [ ] ThreadingVisualization
- [ ] CheckpointBranching
- [ ] ShareModal
- [ ] ProjectPicker

---

## Implementation Checklist

- [X] Extract design tokens from wireframes
- [X] Document color palette (light + dark)
- [X] Document typography scale
- [X] Document spacing system
- [X] Document component specs
- [ ] Update Tailwind config with tokens
- [ ] Create base UI components (shadcn/ui)
- [ ] Implement dark mode toggle
- [ ] Build component library
- [ ] Test responsive layouts
- [ ] Validate accessibility

---

**Last Updated**: 2026-01-10
**Maintainer**: Claude Agent Team
