# OmniAegis Unified Design System
> **Complete specification combining DESIGN.md (product UX & tokens), linear.app (global layout & sidebar), and sentry (table patterns, badges, alert semantics)**
> 
> **For Claude, Copilot, Cursor agents:** Reference this file for all frontend design decisions.

---

## TABLE OF CONTENTS
1. [Project Context & UX Philosophy](#1-project-context--ux-philosophy)
2. [Master Color System](#2-master-color-system)
3. [Typography & Font Stack](#3-typography--font-stack)
4. [Spacing, Grid & Layout System](#4-spacing-grid--layout-system)
5. [Component Library](#5-component-library)
6. [Global Layout Architecture](#6-global-layout-architecture)
7. [Page Specifications](#7-page-specifications)
8. [Interaction Patterns](#8-interaction-patterns)
9. [Motion & Animation](#9-motion--animation)
10. [Accessibility Guidelines](#10-accessibility-guidelines)
11. [Tailwind Configuration](#11-tailwind-configuration)
12. [Developer Handoff](#12-developer-handoff)

---

## 1. PROJECT CONTEXT & UX PHILOSOPHY

### The OmniAegis North Star
OmniAegis is a **control room for ML auditing, explainability, and policy compliance**. It serves five distinct user personas:

| User | Primary Goal | Pain Point if UI Fails |
|------|--------------|------------------------|
| **ML Auditor** | Rapidly assess if an AI decision is trustworthy | Spends 20+ min per case digging through logs |
| **HITL Reviewer** | Accept/reject borderline outputs, annotate regions | Decision fatigue from poor task layout |
| **Policy Officer** | Verify audit trail, confirm smart-contract anchoring | Cannot export immutable proof |
| **MLOps Engineer** | Monitor drift, swap versions, check CI gate | Blind to silent degradation |
| **Data Scientist (XAI)** | Inspect saliency, UMAP clusters, counterfactuals | Saliency overlay unreadable, UMAP not drillable |

### Three Core UX Principles

1. **Density with Clarity** — Pack information, but never overwhelm. Use progressive disclosure & context panels.
2. **Trust Signals First** — Confidence scores, calibration, audit chain status always visible above the fold.
3. **Action in Context** — Approval, rejection, annotation happen in the same view as the data. No modal-first workflows.

**Guiding Metaphor:** Figma meets Linear meets Sentry — a workspace where auditors enter flow state.

---

## 2. MASTER COLOR SYSTEM

### 2.1 Core Palette (CSS Custom Properties)

```css
:root {
  /* ====== BASE SURFACES (Dark-mode primary) ====== */
  --color-bg-primary:        #0D0E12;   /* Main canvas — near-black */
  --color-bg-secondary:      #13151C;   /* Sidebar, panels */
  --color-bg-tertiary:       #1A1D27;   /* Cards, table rows */
  --color-bg-elevated:       #21253A;   /* Modals, popovers, dropdowns */
  
  /* ====== BORDERS ====== */
  --color-border-default:    #2A2E45;   /* Subtle separators */
  --color-border-strong:     #3D4260;   /* Active panels, focus rings */
  --color-border-subtle:     rgba(255,255,255,0.05);   /* Ultra-subtle (from Linear) */
  --color-border-standard:   rgba(255,255,255,0.08);   /* Standard (from Linear) */

  /* ====== BRAND ACCENT — Electric Indigo ====== */
  --color-accent:            #6C63FF;   /* Primary CTA, active states */
  --color-accent-hover:      #7B74FF;   /* Hover shade */
  --color-accent-muted:      #6C63FF22; /* Chip backgrounds, hover fills (13% opacity) */
  --color-accent-glow:       #6C63FF44; /* Focus ring glow (27% opacity) */

  /* ====== SEMANTIC STATUS (Confidence & Policy) ====== */
  --color-success:           #22D3A0;   /* Approved, healthy, compliant (≥0.80 confidence) */
  --color-success-bg:        #22D3A015; /* Success background tint */
  --color-warning:           #F5A623;   /* Low confidence, pending review (0.20–0.79) */
  --color-warning-bg:        #F5A62315; /* Warning background tint */
  --color-danger:            #FF4D6A;   /* Violation, rejected, high risk (<0.20) */
  --color-danger-bg:         #FF4D6A15; /* Danger background tint */
  --color-neutral:           #8B93B0;   /* No decision, unknown */
  --color-neutral-bg:        #8B93B015; /* Neutral background tint */

  /* ====== TEXT ====== */
  --color-text-primary:      #E8EAF6;   /* Headings, labels, primary content */
  --color-text-secondary:    #8B93B0;   /* Supporting text, metadata */
  --color-text-tertiary:     #62666D;   /* Most subdued text — timestamps, disabled */
  --color-text-disabled:     #4A5070;   /* Disabled state text */
  --color-text-inverse:      #0D0E12;   /* Text on accent backgrounds */

  /* ====== HEATMAP OVERLAY (XAI-specific) ====== */
  --color-heatmap-high:      rgba(255, 77, 106, 0.75);   /* Red — high saliency */
  --color-heatmap-mid:       rgba(245, 166, 35, 0.55);   /* Orange — mid saliency */
  --color-heatmap-low:       rgba(34, 211, 160, 0.30);   /* Green — low saliency */

  /* ====== ELEVATION & SHADOWS ====== */
  --shadow-sm:               0 1px 3px rgba(0,0,0,0.4);
  --shadow-md:               0 4px 16px rgba(0,0,0,0.5);
  --shadow-lg:               0 12px 40px rgba(0,0,0,0.6);
  --shadow-glow:             0 0 0 2px var(--color-accent-glow);
  --shadow-inset:            rgba(0,0,0,0.2) 0px 0px 12px inset;
}

/* ====== LIGHT THEME ====== */
[data-theme="light"] {
  --color-bg-primary:        #F5F6FA;
  --color-bg-secondary:      #FFFFFF;
  --color-bg-tertiary:       #ECEEF5;
  --color-bg-elevated:       #FFFFFF;
  --color-border-default:    #DDE0ED;
  --color-border-strong:     #B8BCCC;
  --color-text-primary:      #12152A;
  --color-text-secondary:    #5A6080;
  --color-text-tertiary:     #8A8F98;
  --color-text-disabled:     #A0A8C0;
}

/* ====== HIGH-CONTRAST MODE ====== */
[data-theme="high-contrast"] {
  --color-bg-primary:        #000000;
  --color-bg-secondary:      #0A0A0A;
  --color-accent:            #A09AFF;
  --color-border-default:    #FFFFFF44;
  --color-text-primary:      #FFFFFF;
  --color-text-secondary:    #CCCCCC;
}
```

### 2.2 Color Token Usage Rules

| Use Case | Token(s) | Example |
|----------|---------|---------|
| **Confidence High (≥0.80)** | `--color-success` | Green dot + "87%" badge |
| **Confidence Mid (0.20–0.79)** | `--color-warning` | Orange dot + "45%" badge |
| **Confidence Low (<0.20)** | `--color-danger` | Red dot (pulsing) + "12%" badge |
| **Approved Decision** | `--color-success` | Status chip: "✓ APPROVED" |
| **Rejected Decision** | `--color-danger` | Status chip: "✗ REJECTED" |
| **Pending Review** | `--color-warning` | Status chip: "⏳ PENDING" |
| **On-Chain Anchored** | `--color-accent` | Chip: "⛓ ANCHORED" |
| **Primary CTA Button** | `--color-accent` bg, `--color-text-inverse` text | "Approve", "Anchor to Chain" |
| **Secondary Button** | `--color-border-default` border, `--color-text-primary` text | "Cancel", "More Info" |
| **Hover/Focus State** | `--color-accent-glow` or `--color-accent-hover` | Interactive element highlight |
| **Disabled State** | `--color-text-disabled` | Grayed-out text, opacity 0.5 |

---

## 3. TYPOGRAPHY & FONT STACK

### 3.1 Font Families

```css
--font-sans:  "Inter", "Geist", system-ui, -apple-system, "Segoe UI", sans-serif;
--font-mono:  "JetBrains Mono", "Fira Code", "Consolas", "Menlo", monospace;
```

**NOTE:** Inter is preferred over Geist for precision. Enable OpenType features `cv01` and `ss03` globally (from Linear best practice) for cleaner geometric letterforms:
```css
body {
  font-feature-settings: "cv01", "ss03";
}
```

### 3.2 Typographic Scale & Hierarchy

| Role | Font | Size (rem) | Weight | Line Height | Letter Spacing | Usage |
|------|------|-----------|--------|-------------|----------------|-------|
| **Display XL** | Inter | 2.0 (32px) | 600 | 1.20 | -0.02em | Metric values, hero numbers |
| **Display Large** | Inter | 1.5 (24px) | 600 | 1.25 | -0.01em | Page titles |
| **Display** | Inter | 1.25 (20px) | 600 | 1.30 | normal | Section headings, card titles |
| **Body Large** | Inter | 1.0625 (17px) | 400 | 1.60 | normal | Feature descriptions |
| **Body Emphasis** | Inter | 1.0625 (17px) | 510 | 1.60 | normal | Emphasized body (Linear signature weight) |
| **Body** | Inter | 0.9375 (15px) | 400 | 1.50 | normal | Standard reading text |
| **Body Medium** | Inter | 0.9375 (15px) | 510 | 1.50 | normal | Navigation, labels |
| **Body Semibold** | Inter | 0.9375 (15px) | 600 | 1.50 | normal | Strong emphasis |
| **Small** | Inter | 0.8125 (13px) | 400 | 1.60 | -0.165px | Secondary text, metadata |
| **Small Medium** | Inter | 0.8125 (13px) | 510 | 1.60 | -0.165px | Emphasized small text |
| **Label** | Inter | 0.75 (12px) | 500–600 | 1.40 | 0.06em | Button text, status chips (uppercase) |
| **Caption** | Inter | 0.75 (12px) | 400 | 1.40 | normal | Timestamps, helper text |
| **Micro** | Inter | 0.625 (10px) | 500 | 1.80 | 0.06em | Badges, micro labels (uppercase) |
| **Monospace (Code)** | JetBrains Mono | 0.8125 (13px) | 400 | 1.50 | normal | TX hashes, audit IDs, code blocks |

### 3.3 Typographic Rules (Mandatory)

1. **All metric/KPI numbers:** Use `--text-2xl` (32px), `--font-semibold` (600), `--tracking-tight` (-0.02em)
2. **ALL-CAPS status labels:** Use `--text-xs` (12px), `--font-medium` (500), `--tracking-wide` (0.06em). Example: "✓ APPROVED"
3. **Code/hash values:** Use `--font-mono`, `--text-sm` (13px). Example: `0x4f2...c9a`
4. **Never mix more than 2 font weights on a single card**
5. **Nav links:** Use `--body-medium` (15px, weight 510) or `--small-medium` (13px, weight 510) per Linear
6. **Respect `prefers-reduced-motion`:** Disable all animations, reduce transitions to ≤100ms

---

## 4. SPACING, GRID & LAYOUT SYSTEM

### 4.1 Spacing Scale (Base 4px)

```css
--space-1:   4px;
--space-2:   8px;
--space-3:   12px;
--space-4:   16px;
--space-5:   20px;
--space-6:   24px;
--space-8:   32px;
--space-10:  40px;
--space-12:  48px;
--space-16:  64px;
--space-20:  80px;
```

### 4.2 Border Radius Scale

| Size | Value | Usage |
|------|-------|-------|
| **Micro** | 2px | Inline badges, toolbar buttons, subtle tags (Sentry style) |
| **Small** | 4px | Small containers, list items, checkboxes |
| **Standard** | 8px | Buttons, inputs, functional elements (Linear/OmniAegis primary) |
| **Comfortable** | 12px | Cards, panels, section containers |
| **Large** | 16px | Modals, drawers, large panels |
| **Pill** | 9999px | Chips, filter pills, status tags, avatars |

### 4.3 Global Layout Architecture

```
┌──────────────────────────────────────────────────────────┐
│  TOP NAV (56px fixed height)                             │
│  Logo | Breadcrumb | Search | Action buttons | Profile   │
├────────────────┬──────────────────────────────────────────┤
│  SIDEBAR       │  MAIN CONTENT AREA                      │
│  240px fixed   │  max-width: 1440px                      │
│  (collapses    │  padding: 0 32px                        │
│  to 64px icon) │                                          │
│                │  ┌────────────────┬──────────────────┐  │
│  • Overview    │  │  PRIMARY PANE  │  CONTEXT PANEL   │  │
│  • Ingest      │  │  flex: 1       │  width: 380px    │  │
│  • Monitor     │  │                │  (slide-in)      │  │
│  • XAI         │  │                │  [Close] [×]     │  │
│  • Audit [3]   │  │                │                  │  │
│  • HITL [12]   │  └────────────────┴──────────────────┘  │
│  • Admin       │                                          │
│                │  Auto-hide on mobile                     │
└────────────────┴──────────────────────────────────────────┘
```

**Key Rules:**
- **Sidebar:** Always shows badge counts (unanchored audits, pending HITL tasks) even when collapsed
- **Context Panel:** Never a route change. Always slide-in from right. Dismiss with `Escape` or `[×]`
- **Main content:** Never horizontally scrolls. Responsive grid collapses on tablet/mobile
- **Breadcrumb:** Always present, shows current page location for keyboard navigation

### 4.4 Responsive Breakpoints (Tailwind)

| Breakpoint | Width | Key Changes |
|------------|-------|-------------|
| **Mobile** | <640px | Single column, hamburger nav, stacked cards |
| **Tablet** | 640–1024px | 2-column grids, sidebar visible, reduced padding |
| **Desktop** | 1024–1440px | 3-column grids, full nav visible, standard padding |
| **Large** | >1440px | Max-width enforced, generous margins |

**Layout Behavior:**
- Hero content: 64px padding → 32px (tablet) → 16px (mobile)
- Feature sections: 80px vertical spacing → 48px (tablet) → 32px (mobile)
- Typography scales: 32px headline → 24px (tablet) → 20px (mobile)

---

## 5. COMPONENT LIBRARY

### 5.1 Confidence Badge (CRITICAL COMPONENT)

The most-used component in OmniAegis. Always pairs with numeric value.

```jsx
<ConfidenceBadge value={0.87} />
// Renders: ● 87%  (color mapped to threshold)
```

**Rules:**
- **High (≥0.80):** `--color-success` (green), filled dot, no animation
- **Mid (0.20–0.79):** `--color-warning` (orange), half-dot, no animation
- **Low (<0.20):** `--color-danger` (red), empty dot, pulse animation at 2s interval
- **Display:** Always show raw decimal rounded to 1 decimal place next to dot
- **Never text-only:** "High" / "Low" is forbidden. Always show the number.
- **Placement:** Every list row, every card, every audit record, every HITL task
- **Font:** `--body` weight 500, size 13px or 12px depending on context
- **Hover:** Show full precision (3 decimal places) in a tooltip

**Example HTML:**
```html
<div class="flex items-center gap-1.5">
  <span class="w-1.5 h-1.5 rounded-full" style="background: var(--color-success);"></span>
  <span class="text-xs font-medium" style="color: var(--color-success);">87%</span>
</div>
```

### 5.2 Status Chip

Sentry-inspired badge component for decision states and policy outcomes.

```jsx
<StatusChip status="approved" | "rejected" | "pending" | "flagged" | "anchored" | "reviewing" />
```

| Status | Icon | Color | Background | Rules |
|--------|------|-------|------------|-------|
| `approved` | ✓ | `--color-success` | `--color-success-bg` | Use for confirmed HITL approval |
| `rejected` | ✗ | `--color-danger` | `--color-danger-bg` | Use for rejected items |
| `pending` | ⏳ | `--color-warning` | `--color-warning-bg` | Use for items awaiting review |
| `flagged` | ⚑ | `--color-danger` | `--color-danger-bg` | Use for policy violations |
| `anchored` | ⛓ | `--color-accent` | `--color-accent-muted` | On-chain proof exists |
| `reviewing` | ◌ | `--color-neutral` | `--color-neutral-bg` | In-progress review |

**Styling:**
- Font: Label weight 600, 12px, ALL-CAPS, letter-spacing 0.06em
- Padding: 4px 8px
- Radius: 4px (micro)
- Never use color alone — always include icon + text
- Hover: Slightly increase background opacity

### 5.3 Data Table (Sentry + Linear Pattern)

High-density, keyboard-accessible table for audit records, ingest lists, model registry.

```jsx
<DataTable
  columns={[
    { key: "id", label: "ID", sortable: true, width: "120px" },
    { key: "confidence", label: "Confidence", sortable: true, render: (val) => <ConfidenceBadge value={val} /> },
    { key: "status", label: "Status", render: (val) => <StatusChip status={val} /> },
  ]}
  rows={[...]}
  onRowClick={(row) => openContextPanel(row)}
/>
```

**Structure:**
- Row height: 44px (comfortable density)
- Sticky header: `position: sticky; top: 0; z-index: 10`
- Alternating fill: odd rows use `--color-bg-tertiary`, even rows use `--color-bg-secondary`
- Sortable columns: show sort indicator on hover for ALL columns; active column always shows direction (↑ ↓)
- Inline row actions: appear on `:hover`, never shown by default (reduces visual noise)
- Multi-select: left checkbox column, bulk action bar slides up from bottom when ≥1 row selected

**Keyboard Navigation:**
- `↑` `↓`: Navigate rows
- `Space`: Select/deselect row
- `Enter`: Open context panel for current row
- `Shift+Space`: Select range from last selected to current

**Pagination:**
- Server-side only (no client-side pagination)
- Show: `[← Prev] [1] [2] ... [N] [Next →]`
- Always show total count: "Showing 1–50 of 1,234 results"
- Jump-to: Input field for direct page navigation

### 5.4 Audit Trail Entry Card (Primary Audit Console Component)

```
┌─────────────────────────────────────────────────────────┐
│ ⛓ Anchored        │  AUDIT-2024-08-14-001              │
├─────────────────────────────────────────────────────────┤
│ Asset ID   img_47f3a2   │  Decision   FLAGGED            │
│ Model v.   v2.3.1       │  Confidence 0.23 ●             │
│ Policy     ContentV3    │  Timestamp  2024-08-14 09:42   │
│ TX Hash    0x4f2...c9a  │  [View on-chain ↗]            │
├─────────────────────────────────────────────────────────┤
│ [Download Evidence] [Export JSON] [Share Link]           │
└─────────────────────────────────────────────────────────┘
```

**Styling:**
- Background: `--color-bg-tertiary` (dark card)
- Border: `1px solid --color-border-default`
- Radius: 12px
- Padding: 16px
- Icon indicators (⛓ anchored, ○ unanchored) color-coded: `--color-accent` or `--color-warning`

**Key Fields (Mandatory):**
- Asset ID (truncated, copy-on-click)
- Decision (status chip)
- Confidence (badge)
- Timestamp (small, secondary text)
- TX Hash (monospace, truncated `0x4f2...c9a` with copy button)
- "View on-chain" link (opens new tab, never in-app)

**Actions (Inline or Hover):**
- Download Evidence Pack (generates signed ZIP: PDF + JSON + merkle proof)
- Export JSON (downloadable JSON with all metadata)
- Share Link (generates shareable audit URL)
- Anchor (if unanchored) — triggers smart-contract transaction modal

### 5.5 XAI Saliency Viewer (Full Component)

```
┌────────────────────────────────────────────────────────┐
│ [Original] [Saliency] [Overlay] [Neighbors]            │
├────────────────────────────────────────────────────────┤
│ ┌──────────────────┐   Saliency Regions               │
│ │                  │   1. Region A  contrib: +0.41 ███│
│ │    [IMAGE]       │   2. Region B  contrib: +0.28 ██ │
│ │  + OVERLAY       │   3. Region C  contrib: -0.12 ▌  │
│ │                  │                                   │
│ └──────────────────┘   Attribution Method              │
│ Opacity ●──────○       • Integrated Gradients (active) │
│ [Export PNG] [Export Regions]                          │
└────────────────────────────────────────────────────────┘
```

**Tabs:**
- Original: Raw image/media
- Saliency: Heatmap only
- Overlay: Image + heatmap overlay (adjustable opacity)
- Neighbors: 3×2 grid of 6 closest assets in embedding space

**Controls:**
- Opacity slider: Real-time overlay control (no re-fetch), range 0–100%
- Attribution method dropdown: Integrated Gradients, SHAP KernelExplainer, GradCAM

**Heatmap Rendering:**
- Dark mode: CSS `mix-blend-mode: multiply`
- Light mode: CSS `mix-blend-mode: screen`
- Color scale: High saliency = red (danger), mid = orange (warning), low = green (success)
- Hover region: Show tooltip with exact contribution value

**Contribution Bar Styling:**
- Positive contribution: `--color-success` bar
- Negative contribution: `--color-danger` bar
- Bar width proportional to absolute contribution magnitude

**Keyboard Support:**
- `←` `→`: Navigate between tabs
- `+` `-`: Adjust opacity
- `Escape`: Close if in popover

### 5.6 HITL Task Card

```
┌────────────────────────────────────────────────────────┐
│ TASK #1847 [img] Assigned to you  ● URGENT             │
├────────────────────────────────────────────────────────┤
│ Asset: img_47f3a2 │ Confidence: 0.23 ● │ Model: v2.3.1 │
│ Policy: ContentV3 │ Priority: HIGH     │ Queue pos: 3   │
├────────────────────────────────────────────────────────┤
│ [Context] [Quick XAI ↗] [Original Asset ↗]             │
├────────────────────────────────────────────────────────┤
│ Annotator Note (required if confidence < 0.40):         │
│ ┌──────────────────────────────────────────────────┐   │
│ │ [Text input — auto-focus if low confidence]     │   │
│ └──────────────────────────────────────────────────┘   │
├────────────────────────────────────────────────────────┤
│ [✗ Reject]                    [✓ Approve]             │
│ (danger border) ←────────────→ (success fill)         │
└────────────────────────────────────────────────────────┘
```

**Card Styling:**
- Background: `--color-bg-tertiary`
- Border: `1px solid --color-border-default`
- Radius: 12px
- Padding: 16px
- Urgency indicator: "URGENT" badge appears if task >24h old + unreviewed (pulses red)

**Button Styling:**
- **Reject button:** Left-aligned, `--color-danger` border (no fill by default), text uppercase, white text
- **Approve button:** Right-aligned, `--color-success` fill, text uppercase, white text
- **Note requirement:** If confidence < 0.40, note field auto-focuses with placeholder: "Please explain your decision..."

**Keyboard Shortcuts (Always Visible in Footer):**
- `A`: Approve
- `R`: Reject (requires confirmation — press R again within 1s to confirm)
- `N`: Focus note input
- `→`: Next task (only if current task is resolved)
- `↑` `↓`: Scroll task details within card

**Animations:**
- Task approval: Checkmark SVG draws in, duration 300ms, easing `spring`
- Task rejection: X SVG draws in, duration 300ms, color flashes danger
- Never auto-submit on keyboard shortcut for Reject — always pause 500ms with "Press R again to confirm" text

### 5.7 UMAP / Scatter Plot (Data Visualization)

Interactive 2D embedding visualization with cohort selection and drill-down.

```jsx
<UMAPPlot
  points={[{ x, y, label, confidence, id, metadata }]}
  colorBy="confidence" | "label" | "status"
  onPointClick={(point) => openContextPanel(point)}
  onCohortSelect={(cohort) => updateRightPanel(cohort)}
/>
```

**Features:**
- Zoomable & pannable (use D3 zoom or react-zoom-pan-pinch)
- Point size: 4px default, 8px on hover, 12px when selected
- Color encoding: `--color-confidence-*` scale by default; toggle to color-by-label or color-by-status
- Selected point: white ring (2px) + glow (`--shadow-glow`), z-index elevated
- Cohort selection: lasso tool (hold Shift + drag), OR box select (hold Ctrl + drag)
- Right panel auto-opens with cohort summary when ≥2 points selected
- Loading state: skeleton of ~200 grey dots at opacity 0.3, fade in real points over 500ms

**Keyboard Navigation:**
- `Z`: Zoom to fit all points
- `Shift + drag`: Lasso select
- `Ctrl + drag`: Box select
- `Delete`: Clear selection
- `↑` `↓` `←` `→`: Pan (hold)
- `+` `-`: Zoom in/out

### 5.8 Navigation Sidebar (Linear-Inspired Layout)

```
┌─────────────────────────────────────┐
│ ● OmniAegis      [━ collapse]       │ 56px header
├─────────────────────────────────────┤
│ ┌─────────────────────────────────┐ │
│ │ [Overview]                      │ │
│ │ ─ Ingest Explorer               │ │
│ │ ─ Model Monitor                 │ │
│ │ ─ XAI Viewer                    │ │
│ │ ─ Audit Console          [3]  ← badge │
│ │ ─ HITL Board           [12]  ← badge │
│ │ ─ Policy Registry               │ │
│ ├─────────────────────────────────┤ │
│ │ ADMIN & SETTINGS                │ │
│ │ ─ Model Registry                │ │
│ │ ─ CI Gate                       │ │
│ │ ─ Team & Access                 │ │
│ ├─────────────────────────────────┤ │
│ │ [?] Docs [🌙] Theme [@] Profile │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
240px fixed width (collapses to 64px)
```

**Styling:**
- Background: `--color-bg-secondary`
- Active item: `--color-accent` left border (3px), `--color-accent-muted` background
- Hover item: `--color-accent-muted` background, text color `--color-text-primary`
- Font: `--body-medium` (15px, weight 510) per Linear spec

**Badge Behavior:**
- Updates via WebSocket — no page refresh needed
- Always visible even in collapsed state (icon-only)
- Color: badge count in `--color-accent` when count > 0
- Examples: "Audit Console [3]" = 3 unanchored audits; "HITL Board [12]" = 12 pending tasks

**Collapsed State (64px):**
- Show icons only
- Tooltips on hover (350ms delay)
- Badge counts still visible (right-aligned)
- Main nav sections collapse; restore on expand

**Mobile Behavior:**
- On <768px: hamburger menu, slide-out sidebar from left
- Overlay backdrop when open
- Close on item click
- Keyboard: `Escape` to close

---

## 6. GLOBAL LAYOUT ARCHITECTURE

### 6.1 Top Navigation Bar (56px Fixed Height)

```html
<header class="h-14 bg-surface-secondary flex items-center px-4">
  <!-- Left: Logo + Breadcrumb -->
  <div class="flex items-center gap-2">
    <LogoMark />
    <Breadcrumb currentPath={breadcrumb} />
  </div>
  
  <!-- Center: (Empty or secondary controls) -->
  
  <!-- Right: Search + Actions + Profile -->
  <div class="flex items-center gap-3 ml-auto">
    <SearchInput />
    <Button variant="ghost" icon="bell" badge={notificationCount} />
    <Divider vertical />
    <ProfileDropdown />
  </div>
</header>
```

**Rules:**
- Logo click: Always navigates home (never disabled)
- Breadcrumb: Max 4 levels, truncate with "…" if deeper
- Search: Command palette trigger (`Cmd+K` or `/`), shows recent searches + filtered results live
- Notifications bell: Badge shows unread count, click opens dropdown menu
- Profile dropdown: Shows name, email, theme toggle, settings link, logout

**Sticky Behavior:**
- Always fixed to top
- Z-index: 100
- Subtle shadow below: `--shadow-sm`

### 6.2 Main Content Area

**Max-width:** 1440px centered, with 32px padding left/right (desktop)

**Responsive:**
- Desktop (>1024px): max-width 1440px, padding 32px
- Tablet (768–1024px): max-width 100%, padding 24px
- Mobile (<768px): max-width 100%, padding 16px

**Content Grid Patterns:**
- **Single column:** Default for detail views, HITL tasks, individual audits
- **Two column:** Audit list + context panel
- **Three column:** Rare; only for comparative views (e.g., Model A vs B vs C)

### 6.3 Context Panel (380px Right Slide-In)

Never a route change. Always overlays main content.

```html
<aside class="fixed right-0 top-14 h-[calc(100vh-56px)] w-96 bg-surface-secondary shadow-lg transform translate-x-full transition-transform">
  <div class="flex items-center justify-between px-4 py-3 border-b border-border-default">
    <h2 class="text-lg font-semibold">Details</h2>
    <button onClick={closePanel} className="text-tertiary hover:text-primary">✕</button>
  </div>
  <div class="overflow-y-auto h-full">
    {panelContent}
  </div>
</aside>
```

**Rules:**
- Width: 380px fixed (never responsive except fully hidden on mobile)
- Slide-in animation: 200ms, easing `ease-out`
- Close trigger: `Escape` key, `[×]` button, or clicking backdrop
- Scrollable: Panel content only, header fixed
- Z-index: 99 (below modals at 100+)
- Mobile (<768px): Full-width modal bottom sheet instead

---

## 7. PAGE SPECIFICATIONS

### 7.1 Overview / Home (Dashboard)

**Layout:** KPI metric strip → 2-col chart row → recent activity table

**Key Metrics Strip (Always Visible Top):**
```
[ Ingested Today ]  [ Decisions Made ]  [ HITL Queue ]  [ Privacy Budget ]
     14,302              9,847                12           ε: 0.73 / 1.0
```

- Metric values: `--text-2xl`, `--font-semibold`, `--tracking-tight`, `--color-text-primary`
- KPI labels: `--text-sm`, `--color-text-secondary`
- Live updates: Count-up animation (duration 600ms) when metrics change
- Privacy budget: Donut chart — green when <80%, orange at 80%, red at 100%
- Privacy warning: Auto-displays banner when ε > 80%: "Privacy budget >80% used — consider model retraining"

**Recent Activity Table:**
- Columns: Timestamp | Asset | Decision | Confidence | Status | Actions
- Rows: 5–10 most recent items, sorted newest first
- Actions on hover: "View Audit", "Rerun XAI"
- Auto-refresh: Every 30s with WebSocket, changed rows animate

**Keyboard Navigation:**
- `←` `→`: Navigate between metric cards
- `Enter`: Open detail for metric (e.g., privacy budget details)
- `↓`: Focus table
- Table nav same as DataTable section

### 7.2 Ingest Explorer

**Layout:** Filter sidebar (280px left) + item grid/list toggle + main content area

**Filter Sidebar:**
- Media type: Checkboxes (image, audio, video, text, mixed)
- Confidence range: Dual-slider (0.0–1.0)
- Date range: Date pickers (from / to)
- Source: Dropdown + multi-select (web scraper, API, batch upload, etc.)
- Status: Checkboxes (new, processing, indexed, error, quarantined)
- Quick filters: Predefined chips ("Last 24h", "Low confidence", "Pending XAI", "Flagged by policy")

**Toggle: Grid vs. List View**
- Grid: 3-column responsive grid, card preview style
- List: Dense table view with thumbnail column (60px)
- User preference persisted in localStorage

**Grid View Card:**
```
┌─────────────────────┐
│   [THUMBNAIL]       │
├─────────────────────┤
│ Asset ID: img_47... │
│ Confidence: 87% ●   │
│ Status: ✓ INDEXED   │
│ Source: web_scraper │
├─────────────────────┤
│ [Quick XAI] [More]  │ (on hover)
└─────────────────────┘
```

**List View Table:**
- Columns: ID (sortable) | Thumbnail | Type | Confidence (sortable) | Status (sortable) | Date (sortable) | Actions
- Row height: 44px
- Multi-select enabled for batch XAI reruns

**Infinite Scroll or Pagination:**
- Infinite scroll preferred: New items slide in from top
- Alternative: Server-side pagination with "Load More" button at bottom
- Live ingest indicator: "Ingesting 342 items..." progress bar at top

### 7.3 Model Monitor / Drift

**Layout:** Top KPI row (accuracy, ECE, data drift) → 2-col: UMAP (left, 60%) + drift timeline (right, 40%)

**Model Version Selector (Top Left):**
- Dropdown showing all active versions
- Each version shows: name, date deployed, current status (active/candidate), accuracy/ECE
- "Swap to..." button for each candidate version

**UMAP Visualization (Left Pane):**
- Interactive scatter plot, color-coded by confidence
- Toggle color encoding: confidence | label | status | drift-direction
- Zooming + panning enabled
- Cohort selection (lasso or box) updates right timeline with cohort's drift curve

**Drift Timeline (Right Pane):**
- Line chart: X-axis = time, Y-axis = metric (accuracy, ECE, or custom)
- Vertical dashed lines: Model swap events
- Hover point: Show exact metric + timestamp
- Shaded region: ±1 std dev confidence interval
- Threshold lines: Accuracy/ECE targets (if configured in admin)

**Keyboard Navigation:**
- `M`: Toggle model selector
- `U`: Reset UMAP zoom/pan to fit
- `T`: Toggle timeline metric (accuracy → ECE → custom)
- `+` `-`: Zoom UMAP

### 7.4 XAI Viewer (Full-Page)

**Context Entry:**
- Always invoked with a specific asset ID (from HITL task, audit record, or ingest explorer)
- Breadcrumb: `Ingest Explorer > img_47f3a2 > XAI Viewer`
- Back button: Returns to invoking page and restores scroll position

**Layout:** Media viewer (left 70%) + saliency breakdown (right 30%)

**Tabs:** Original | Saliency | Overlay | Neighbors (described in Section 5.5)

**Export Options:**
- Export PNG: Download current view (with saliency overlay if showing)
- Export Regions JSON: Download region contribution data for external analysis
- Export Full Report: PDF with all tabs, metadata, contribution table

**Keyboard Navigation:**
- `←` `→`: Navigate tabs
- `+` `-`: Adjust overlay opacity
- `D`: Download current view
- `Escape`: Return to previous page

### 7.5 Audit Console (HIGHEST PRIORITY PAGE)

**Layout:** Filter bar (sticky top) + sortable table + context panel (slide-in)

**Filter Bar:**
- Policy name: Dropdown + multi-select
- Status: Tabs (All | Unanchored | Anchored | Flagged | Reviewed)
- Confidence range: Dual-slider
- Date range: Date pickers
- Model version: Dropdown
- Search: Full-text search across audit IDs, asset IDs, policy names

**Default Sort:** Most recent first, unanchored items float to top (always appear first)

**Table Columns:**
| Column | Sortable | Width | Content |
|--------|----------|-------|---------|
| **Anchor Status** | No | 40px | Icon (⛓ anchored or ○ unanchored) |
| **ID** | Yes | 120px | AUDIT-2024-08-14-001 (copy-on-click) |
| **Asset ID** | Yes | 120px | img_47f3a2 (truncated, hover for full) |
| **Decision** | Yes | 80px | Status chip (✓ APPROVED, ✗ REJECTED, etc.) |
| **Confidence** | Yes | 100px | Badge ● 87% |
| **Policy** | Yes | 100px | ContentV3 |
| **Model** | Yes | 80px | v2.3.1 |
| **Timestamp** | Yes | 140px | 2024-08-14 09:42 UTC |
| **Actions** | No | 120px | "View Audit" button, inline on hover |

**Row Expand (Without Panel):**
- Click anywhere on row → Context Panel opens (right slide-in)
- Or: Double-click → Opens inline evidence preview (no panel, reduces clicks)

**Bulk Anchor Action:**
- Select multiple unanchored audits via left checkboxes
- Bulk action bar slides up from bottom: "[N selected] [Clear] [Anchor All] [Export Selected]"
- "Anchor All": Batch smart-contract transaction confirmation
- Show estimated gas fee + TX preview before confirming

**Evidence Download (Per Audit):**
- Hover row → "Download Evidence Pack" button appears
- Generates signed ZIP containing: PDF (formatted audit), JSON (all metadata), merkle proof

**Context Panel Content (On Row Click):**
- Audit header (ID, status chip, timestamp)
- Asset preview (thumbnail + metadata)
- XAI preview (top 3 saliency regions inline)
- Policy details (which policy triggered, threshold values)
- TX hash (if anchored) with "View on-chain" link
- Action buttons: "Anchor", "Download Evidence", "Export JSON", "Share Audit Link"

### 7.6 HITL Board

**View Toggle:** Kanban (column drag-drop) OR List (dense table)

**Kanban View (Default):**
```
┌──────────────┬──────────────┬──────────────┬──────────────┐
│ Assigned (5) │ In Review(3) │ Conflict (1) │ Resolved(42) │
├──────────────┼──────────────┼──────────────┼──────────────┤
│ ┌──────────┐ │ ┌──────────┐ │ ┌──────────┐ │ (archived)   │
│ │ TASK 847 │ │ │ TASK 921 │ │ │ TASK 756 │ │              │
│ │ 0.23 ●   │ │ │ 0.56 ●   │ │ │ 0.67 ●   │ │              │
│ │[Drag⇄]   │ │ │[Drag⇄]   │ │ │[Drag⇄]   │ │              │
│ └──────────┘ │ └──────────┘ │ └──────────┘ │              │
│              │              │              │              │
│ ┌──────────┐ │              │              │              │
│ │ TASK 854 │ │              │              │              │
│ │ 0.35 ●   │ │              │              │              │
│ └──────────┘ │              │              │              │
└──────────────┴──────────────┴──────────────┴──────────────┘
```

- Drag card between columns to change task status
- Update API immediately on drop (with undo if failed)
- "Conflict" column: Shows tasks with ≥2 conflicting annotations — requires supervisor decision
- "Resolved" column: Archived items (hidden by default, show via checkbox)

**List View:**
- Table with columns: ID | Assigned To | Asset | Confidence | Priority | Status | Date Created
- Multi-select for bulk status change
- Sorting enabled on all columns
- Inline notes visible (truncated with "…", expand on hover)

**Keyboard Shortcut Bar (Always Visible Bottom):**
```
[A] Approve  [R] Reject  [N] Note  [→] Next Task  [← Previous]
```

- Shortcuts apply to currently selected/focused task
- Visual indicator shows which task is "active" (bold border)

**Task Card Details (When Selected):**
Opens as side panel on desktop, modal on mobile. Contains:
- Full task metadata (asset, confidence, policy, model)
- XAI preview (inline saliency regions)
- Annotation canvas (if image: polygon/box drawing; if video: timestamp markers)
- Reviewer note field (required if confidence < 0.40)
- Approval/Rejection buttons with confirmation

**Real-Time Collaboration:**
- Show which user(s) are currently reviewing a task (in card header)
- Prevent duplicate review: Lock task for current user when opened
- Live note updates: Show other reviewers' notes in real-time (small badge: "Reviewer added note")

### 7.7 Admin & Settings

**Left Menu Tabs (Always Visible):**
- Model Registry
- CI Gate
- Uploads
- Team & Access
- Audit Policies
- API Keys

**Model Registry Tab:**
- Table of all model versions: name, date deployed, accuracy, ECE, active/inactive toggle
- "Set as Active" CTA for each candidate version (with swap confirmation)
- Model rollback: Emergency button to revert to previous version (requires confirmation + reason)
- Performance comparison: Toggle A/B side-by-side for two selected models

**CI Gate Tab:**
- Confidence threshold slider (global): 0.0–1.0, default 0.50
- ECE (Expected Calibration Error) threshold slider: 0.0–0.50
- Live preview: "Adjusting threshold to 0.60 would flag 342 of 10,847 past decisions (3.2%)"
- Bypass duration: Dropdown to temporarily disable gate (1h, 4h, 24h, custom)
- Audit trail: Log of all threshold changes + who changed them

**Uploads Tab:**
- Batch upload widget: Drag-drop or file picker, accepts zip/csv/json
- Progress bar: Real-time ingest progress
- Preview: Show sample rows from CSV before confirming
- Success/error report: JSON download after batch completes

**Team & Access Tab:**
- User list: Name, email, role, last login, action buttons (revoke, edit, delete)
- Roles: Admin | Auditor | Reviewer | Engineer (permission matrix shown on hover)
- Invite new user: Form with email, role selector, "Send Invite" button
- Audit log: All access changes logged with timestamp + actor

**Audit Policies Tab:**
- Policy definitions: Name, description, rules (confidence threshold, content filters, etc.)
- Policy history: Version control with rollback to previous policy
- Test policy: Upload sample data to see how many items would be flagged

**API Keys Tab:**
- List of generated API keys: Name, last used, created date, action buttons (revoke, copy, rotate)
- "Generate New Key" button
- Key display (only once): Copy button + warning to save securely

---

## 8. INTERACTION PATTERNS

### 8.1 Real-Time Updates

**WebSocket/SSE for:**
- HITL queue count badge (updates instantly)
- Ingest progress bar (when batch upload in progress)
- CI gate status changes
- New audit records appearing at top of Audit Console

**Animation on Change:**
- Badge count: 300ms count-up animation
- New list items: Slide-in from top, highlight (yellow fade) for 3 seconds
- Status change: Chip color flash + smooth transition

### 8.2 Loading States

**Skeleton Screens (Always Show):**
- Data tables: 8 skeleton rows, same height as real rows
- UMAP: Grid of 200 grey dots at 30% opacity, fade in real points over 500ms
- Saliency: Image placeholder with skeleton "regions" list on right
- Charts: Skeleton axis + gridlines, then fade in data

**Progress Indicators:**
- Long operations (>500ms): Inline progress bar in triggering button
- Button text changes: "Anchoring..." → "Anchor" (on completion)
- Cancelable operations: Show `[Cancel]` button while loading

**Error States:**
- API error: Toast notification, bottom-right, `--color-danger`, includes error code
- Recoverable error: Inline in affected component with "Retry" button
- Offline: Persistent banner at top of page (never toast)

### 8.3 Empty States

Never show bare "No data" messages. Always explain why and provide action:

- **HITL Board empty:** "No tasks in queue. The model is operating with high confidence. ✓"
- **Audit Console empty:** "All audits are anchored and up to date. ✓"
- **Ingest Explorer empty:** "No ingested items yet. [Start ingesting data →]"
- **Search results empty:** "No results for '{query}'. Try different filters or date range."

### 8.4 Confirmation Patterns

**Destructive Actions (Reject, Rollback, Delete):**
- Confirmation chip: Type word to proceed (e.g., "Type 'CONFIRM' to proceed")
- Never auto-submit on keyboard shortcut — pause 500ms with visual prompt: "Press R again to confirm"

**High-Value Transactions (Anchor to Smart Contract):**
- Show estimated gas fee
- Preview TX data (to/from, data hash)
- Explicit confirmation button: "Yes, anchor to chain"
- TX hash provided after success with "View on-chain" link

### 8.5 Command Palette

Triggered by `Cmd+K` (Mac) or `Ctrl+K` (Windows), or `/` on any page.

```
┌─────────────────────────────────────────┐
│ / Search actions or pages...            │
├─────────────────────────────────────────┤
│ Recent Searches                          │
│ • Model swap to v2.3.1                   │
│ • AUDIT-2024-08-14-001                   │
│                                          │
│ Pages                                    │
│ • Audit Console                          │
│ • HITL Board                             │
│ • Model Monitor                          │
│                                          │
│ Actions                                  │
│ • Create new audit                       │
│ • Download evidence pack                 │
│ • Invite team member                     │
└─────────────────────────────────────────┘
```

**Keyboard Navigation:**
- `↓` `↑`: Navigate results
- `Enter`: Select item
- `Escape`: Close
- Fuzzy search on page titles and action names

---

## 9. MOTION & ANIMATION

### 9.1 Easing & Duration

```css
/* Easing Functions */
--ease-out:    cubic-bezier(0.0, 0.0, 0.2, 1.0);    /* Standard exit */
--ease-in-out: cubic-bezier(0.4, 0.0, 0.2, 1.0);    /* Standard move */
--ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1.0); /* Bouncy entry */

/* Durations */
--duration-fast:    100ms;  /* Hover fills, badge updates */
--duration-normal:  200ms;  /* Panel open/close, tab switch */
--duration-slow:    350ms;  /* Page transitions, modal appear */
--duration-crawl:   600ms;  /* Count-up animations, chart draw */
```

### 9.2 Animation Applications

| Animation | Duration | Easing | Use |
|-----------|----------|--------|-----|
| **Panel slide-in** | 200ms | ease-out | Context panel from right |
| **Modal appear** | 350ms | ease-spring | opacity 0→1, scale 0.96→1 |
| **Badge count-up** | 600ms | ease-out | Metric value increment |
| **List item slide** | 200ms | ease-out | New item enters from top |
| **Checkbox checked** | 100ms | ease-in-out | SVG path draw + checkmark |
| **Confidence low pulse** | 2s infinite | ease-in-out | Only for <0.20 confidence |
| **Tab switch** | 200ms | ease-out | Opacity + translateX (-20px) |
| **Hover fill** | 100ms | ease-out | Button background color |

### 9.3 Accessibility Rule

**Respect `prefers-reduced-motion`:**
```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

All animations disabled; transitions ≤100ms only.

---

## 10. ACCESSIBILITY GUIDELINES (WCAG AA Minimum)

### 10.1 Color Contrast

- **Text on background:** Ratio ≥4.5:1 for body text (AA), ≥7:1 for headings (AAA preferred)
- **Component borders:** Ratio ≥3:1 for interactive elements
- **Status indicators:** Color NEVER the only differentiator. Always include icon + text.

**Test with:** WebAIM Contrast Checker, axe DevTools, Lighthouse

### 10.2 Keyboard Navigation

**Tab Order:**
- Logical flow: top to bottom, left to right
- Modal trap: Focus trapped within modal until dismiss (Escape or button)
- Skip link: "Skip to main content" link (visible on focus)

**Keyboard Shortcuts (Always Accessible):**
- HITL: `A` (Approve), `R` (Reject), `N` (Note), `→` (Next)
- Audit: `Shift+A` (Anchor), `Cmd+S` (Save/Export)
- Global: `Cmd+K` (Search/Command Palette), `Escape` (Close panels/modals)

**Focus Indicator:**
- Ring: `box-shadow: var(--shadow-glow)` (2px offset)
- Color: `--color-accent` (never removed)
- Visible on ALL interactive elements

### 10.3 Screen Reader Support

**ARIA Semantics:**
- Modals: `role="dialog"`, `aria-modal="true"`, `aria-label`
- Tables: `<thead>`, `<tbody>`, `<th scope="col">`, `<caption>`
- Live regions: `aria-live="polite"` for toast notifications, batch progress
- Landmarks: `<nav>`, `<main>`, `<aside>` (semantic HTML preferred)
- Form labels: `<label for="id">` or `aria-label`

**Live Regions (Examples):**
```html
<!-- Batch anchor progress -->
<div aria-live="polite" aria-atomic="true">
  Anchoring 5 of 12 audits...
</div>

<!-- Saliency regions list (for color-blind users) -->
<div aria-live="polite" role="region" aria-label="Saliency regions">
  <ol>
    <li>Region A: +0.41 (top-left corner)</li>
    <li>Region B: +0.28 (center)</li>
  </ol>
</div>
```

### 10.4 Color Blindness (Protanopia / Deuteranopia)

**Heatmap Overlay:** Provide alternative visual encoding
```css
/* Primary: Red-Yellow-Green */
/* Secondary: Solid circle (size) + stroke (width) encoding */
```

**Status Chips:** Use both color + icon:
- `--color-success` + ✓ icon (not green alone)
- `--color-danger` + ✗ icon (not red alone)

**Charts:** Legend always visible, colors differentiated by saturation/brightness not hue alone

### 10.5 Touch Targets

- **Minimum:** 44×44 px (WCAG AAA)
- Mobile-optimized buttons: Padding 12px 16px (≥44px touch target)
- Icon buttons: 44×44px minimum
- Form inputs: Height ≥44px

### 10.6 Mobile & Tablet Accessibility

- **Viewport meta tag:** `<meta name="viewport" content="width=device-width, initial-scale=1">`
- **Orientation:** Support both portrait + landscape
- **Touch mode:** Increase touch targets by 20% on mobile
- **Text size:** Never < 16px (prevents iOS auto-zoom)

---

## 11. TAILWIND CONFIGURATION

```typescript
// tailwind.config.ts — extend section

module.exports = {
  darkMode: ['class', '[data-theme="dark"]'],
  theme: {
    extend: {
      colors: {
        /* Primary Surfaces */
        surface: {
          primary:   '#0D0E12',
          secondary: '#13151C',
          tertiary:  '#1A1D27',
          elevated:  '#21253A',
        },
        /* Brand Accent */
        accent: {
          DEFAULT: '#6C63FF',
          hover:   '#7B74FF',
          muted:   '#6C63FF22',
          glow:    '#6C63FF44',
        },
        /* Semantic Status */
        status: {
          success: '#22D3A0',
          warning: '#F5A623',
          danger:  '#FF4D6A',
          neutral: '#8B93B0',
        },
        /* Borders */
        border: {
          DEFAULT:  '#2A2E45',
          strong:   '#3D4260',
          subtle:   'rgba(255, 255, 255, 0.05)',
          standard: 'rgba(255, 255, 255, 0.08)',
        },
        /* Text */
        text: {
          primary:   '#E8EAF6',
          secondary: '#8B93B0',
          tertiary:  '#62666D',
          disabled:  '#4A5070',
        },
      },
      fontFamily: {
        sans: ['Inter', 'Geist', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace'],
      },
      fontSize: {
        '2xs': ['0.625rem', { lineHeight: '1rem' }],
        'xs':  ['0.75rem',  { lineHeight: '1.4' }],
        'sm':  ['0.8125rem', { lineHeight: '1.6' }],
        'base': ['0.9375rem', { lineHeight: '1.5' }],
        'md':  ['1.0625rem', { lineHeight: '1.6' }],
        'lg':  ['1.25rem', { lineHeight: '1.3' }],
        'xl':  ['1.5rem', { lineHeight: '1.25' }],
        '2xl': ['2rem', { lineHeight: '1.2' }],
      },
      fontWeight: {
        normal:    400,
        medium:    500,
        semibold:  600,
        bold:      700,
      },
      boxShadow: {
        sm:   '0 1px 3px rgba(0,0,0,0.4)',
        md:   '0 4px 16px rgba(0,0,0,0.5)',
        lg:   '0 12px 40px rgba(0,0,0,0.6)',
        glow: '0 0 0 2px #6C63FF44',
      },
      transitionTimingFunction: {
        spring: 'cubic-bezier(0.34, 1.56, 0.64, 1.0)',
      },
      transitionDuration: {
        fast:   '100ms',
        normal: '200ms',
        slow:   '350ms',
        crawl:  '600ms',
      },
      borderRadius: {
        sm: '4px',      /* Badges, small buttons */
        md: '8px',      /* Buttons, inputs, cards (standard) */
        lg: '12px',     /* Large cards, panels */
        xl: '16px',     /* Modals, drawers */
        full: '9999px', /* Pills, avatars */
      },
    },
  },
};
```

---

## 12. DEVELOPER HANDOFF

### 12.1 Component Library Organization

```
src/
├── components/
│   ├── ui/                          /* Reusable atomic components */
│   │   ├── ConfidenceBadge.tsx      /* CRITICAL — used everywhere */
│   │   ├── StatusChip.tsx           /* Status indicators */
│   │   ├── DataTable.tsx            /* High-density tables */
│   │   ├── Button.tsx               /* Primary, secondary, ghost variants */
│   │   ├── Input.tsx                /* Text, select, range inputs */
│   │   ├── Modal.tsx                /* Confirmation, full-page modals */
│   │   ├── ContextPanel.tsx         /* Right slide-in panel */
│   │   └── Toast.tsx                /* Notifications */
│   ├── xai/                         /* Explainability components */
│   │   ├── SaliencyViewer.tsx       /* Full saliency viewer */
│   │   ├── UMAPPlot.tsx             /* Interactive scatter plot */
│   │   ├── NeighborGrid.tsx         /* Similar assets grid */
│   │   └── HeatmapOverlay.tsx       /* Image + heatmap composite */
│   ├── audit/                       /* Audit-specific components */
│   │   ├── AuditTrailEntry.tsx      /* Card for audit records */
│   │   ├── AuditTable.tsx           /* Audit list table */
│   │   └── EvidencePackDownload.tsx /* Evidence download modal */
│   ├── hitl/                        /* HITL workflow components */
│   │   ├── TaskCard.tsx             /* Single task card */
│   │   ├── TaskBoard.tsx            /* Kanban + list views */
│   │   ├── AnnotationCanvas.tsx     /* Image annotation tool */
│   │   └── TaskKeyboardShortcuts.tsx /* Shortcut bar + handler */
│   ├── layout/                      /* Global layout shell */
│   │   ├── TopNav.tsx               /* Header bar */
│   │   ├── Sidebar.tsx              /* Left navigation */
│   │   ├── MainLayout.tsx           /* Top + sidebar + main + context */
│   │   └── ContextPanel.tsx         /* Right slide-in overlay */
│   └── charts/                      /* Data visualization */
│       ├── LineChart.tsx            /* Drift timeline */
│       ├── ConfusionMatrix.tsx      /* Model evaluation */
│       └── DonutChart.tsx           /* Privacy budget gauge */
├── pages/ (or app/)
│   ├── overview/
│   ├── ingest/
│   ├── monitor/
│   ├── xai/
│   ├── audit/
│   ├── hitl/
│   └── admin/
├── hooks/                           /* Custom React hooks */
│   ├── useContextPanel.ts           /* Open/close right panel */
│   ├── useWebSocket.ts              /* Real-time updates */
│   ├── useKeyboardShortcuts.ts      /* Global shortcuts */
│   └── useConfidenceBadge.ts        /* Confidence color logic */
├── styles/
│   ├── globals.css                  /* CSS custom properties */
│   ├── tokens.css                   /* Typography + spacing tokens */
│   └── animations.css               /* Keyframe definitions */
├── utils/
│   ├── colors.ts                    /* Color mappings (confidence → token) */
│   ├── formatters.ts                /* Number, date, hash formatting */
│   └── validators.ts                /* Form validation */
└── types/
    ├── audit.ts                     /* Audit record shape */
    ├── hitl.ts                      /* HITL task shape */
    └── xai.ts                       /* XAI response shape */
```

### 12.2 Storybook Setup

```bash
npm run storybook
```

**Key Stories to Create:**

1. **ConfidenceBadge.stories.tsx**
   - High (0.87) — green
   - Mid (0.45) — orange
   - Low (0.12) — red + pulsing

2. **StatusChip.stories.tsx**
   - All 6 status types (approved, rejected, pending, flagged, anchored, reviewing)
   - With + without icon
   - Hover states

3. **DataTable.stories.tsx**
   - Empty state
   - Loading skeleton
   - With multi-select
   - With inline row actions
   - Sorted columns

4. **AuditTrailEntry.stories.tsx**
   - Anchored + unanchored
   - Different confidence levels
   - Actions (download, export, share)

5. **UMAPPlot.stories.tsx**
   - Full plot with 1000 points
   - Cohort selection demo
   - Loading skeleton

6. **TaskCard.stories.tsx**
   - Urgent task (>24h old)
   - Low confidence (requires note)
   - Keyboard shortcuts visible

### 12.3 Design Tokens Export

Generate JSON tokens for Figma → Tailwind sync:

```json
{
  "colors": {
    "surface-primary": "#0D0E12",
    "surface-secondary": "#13151C",
    "accent": "#6C63FF",
    "success": "#22D3A0",
    "warning": "#F5A623",
    "danger": "#FF4D6A",
    "text-primary": "#E8EAF6"
  },
  "typography": {
    "heading-xl": {
      "fontSize": "2rem",
      "fontWeight": 600,
      "lineHeight": 1.2,
      "letterSpacing": "-0.02em"
    },
    "body": {
      "fontSize": "0.9375rem",
      "fontWeight": 400,
      "lineHeight": 1.5
    }
  },
  "spacing": {
    "1": "4px",
    "2": "8px",
    "4": "16px",
    "6": "24px"
  },
  "shadows": {
    "sm": "0 1px 3px rgba(0,0,0,0.4)",
    "glow": "0 0 0 2px #6C63FF44"
  }
}
```

### 12.4 QA Checklist

- [ ] Confidence badges appear on all list rows + cards
- [ ] Status chips use icon + text (never color-only)
- [ ] Context panel doesn't break main content on mobile
- [ ] HITL keyboard shortcuts work globally (A, R, N, →)
- [ ] UMAP zoomable + pannable without lag
- [ ] Saliency heatmap overlays don't obscure image on dark mode
- [ ] All modals have focus trap + Escape dismissal
- [ ] Audit table sortable, multi-select works
- [ ] Privacy budget donut chart updates in real-time
- [ ] WebSocket reconnection doesn't break UI state
- [ ] Dark/light/high-contrast themes all work
- [ ] Lighthouse accessibility score ≥95
- [ ] Keyboard-only navigation works end-to-end
- [ ] No hardcoded color values in components (all use CSS vars)

### 12.5 API Integration Points

**Endpoints Consumed by Frontend:**

| Endpoint | Purpose | Example Response |
|----------|---------|------------------|
| `GET /api/audits` | Fetch audit list with filters | `{ audits: [...], total: 1234, page: 1 }` |
| `POST /api/audits/{id}/anchor` | Anchor audit to smart contract | `{ txHash: "0x4f2...", status: "pending" }` |
| `GET /api/xai/saliency?asset_id=...` | Fetch saliency regions | `{ regions: [...], method: "integrated_gradients" }` |
| `GET /api/xai/neighbors?asset_id=...` | Fetch similar assets | `{ neighbors: [...], distances: [...] }` |
| `GET /api/hitl/tasks` | Fetch HITL task queue | `{ tasks: [...], counts: { assigned: 5, ... } }` |
| `POST /api/hitl/tasks/{id}/decision` | Submit HITL decision | `{ taskId, decision, note, timestamp }` |
| `GET /api/models` | Fetch all model versions | `{ models: [...], active: "v2.3.1" }` |
| `POST /api/models/{id}/activate` | Swap to new model version | `{ modelId, txHash, status }` |
| `GET /api/drift?model_id=...&window=...` | Fetch drift metrics | `{ timeline: [...], umap: [...] }` |

**WebSocket Events (Real-Time):**
- `audit:new` — New audit record created
- `hitl:task:assigned` — New task assigned to current user
- `model:swapped` — Model version changed
- `ingest:progress` — Batch ingest progress update
- `queue:updated` — HITL queue count changed

---

## SUMMARY FOR CLAUDE / AI AGENTS

### Use This File For:
- ✅ All color decisions → Section 2 (Master Color System)
- ✅ Typography rules → Section 3
- ✅ Component styling → Section 5 (especially ConfidenceBadge, StatusChip, DataTable)
- ✅ Global layout → Section 6 (sidebar, context panel, responsive)
- ✅ Page specifications → Section 7 (exact requirements per page)
- ✅ Accessibility requirements → Section 10 (WCAG AA, keyboard nav, screen readers)
- ✅ Tailwind config → Section 11 (plug-and-play theme extension)

### Do NOT Deviate From:
- ❌ Color tokens (Section 2.1) — no hardcoded hex values
- ❌ Typography hierarchy (Section 3.2) — strict scale adherence
- ❌ Spacing scale (Section 4.1) — only use defined values
- ❌ Component patterns (Section 5) — consistency critical for flow state
- ❌ Accessibility rules (Section 10) — WCAG AA minimum non-negotiable

### Key Rules:
1. **Confidence badge:** Every list row, card, audit record, HITL task
2. **Status chips:** Icon + text, never color-only
3. **Context panel:** Right slide-in, no route change
4. **Keyboard shortcuts:** HITL uses A/R/N/→, global search uses Cmd+K
5. **Real-time:** WebSocket updates for queue counts, ingest progress, status changes
6. **No modal-first:** Actions happen in context, panels open, not new pages

---

*Unified design specification for OmniAegis combining DESIGN.md (UX + tokens), linear.app/DESIGN.md (layout + sidebar), and sentry/DESIGN.md (tables, badges, alerts).*

*Generated for seamless handoff to Claude, Copilot, Cursor, and frontend engineers.*

*Last updated: April 28, 2026*
