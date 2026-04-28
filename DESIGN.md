# DESIGN.md — OmniAegis / SentinelAgent UI System
> **For AI coding agents (Copilot, Cursor, Claude Code, etc.)**  
> Drop this file in your project root. Reference it in every UI prompt: "Follow DESIGN.md".

---

## 0. PM PRODUCT CONTEXT — WHO IS USING THIS AND HOW

Before any pixel, understand the users and their mental model.

### Primary Users & Their Jobs-To-Be-Done

| User Persona | Core Job | Pain if UI fails |
|---|---|---|
| **ML Auditor** | Rapidly assess whether an AI model decision is trustworthy and explainable | Spends 20+ min per case digging through logs instead of 2 min |
| **HITL Reviewer** | Accept/reject borderline model outputs, annotate regions, resolve conflicts | Decision fatigue from poor task layout; context loss between items |
| **Policy Compliance Officer** | Verify audit trail, confirm smart-contract anchoring, generate evidence packages | Cannot export or cite immutable proof; no clear chain of custody |
| **ML Engineer / MLOps** | Monitor model drift, swap versions, check CI gate health | Blind to silent degradation; model swap requires code knowledge |
| **Data Scientist (XAI)** | Inspect saliency maps, UMAP clusters, counterfactuals to trust model outputs | Saliency overlay is unreadable; UMAP has no cohort drill-down |

### The "Stream-Like Experience" Principle (PM North Star)

OmniAegis should feel like **Figma meets Linear meets Sentry** — a workspace where an auditor enters a flow state:  
- Zero unnecessary navigation hops (max 2 clicks to any critical action)  
- Every page has one dominant action and a persistent context panel  
- Background jobs surface results in-place — no "go refresh" moments  
- Confidence scores and alert states are always visible, never buried

---

## 1. DESIGN PHILOSOPHY

**Guiding Metaphor:** A control room, not a dashboard grid.  
High-stakes, data-dense, always-on. Calm by default; urgent when it matters.

**Four Design Principles:**
1. **Density with Clarity** — pack information, but never overwhelm. Use progressive disclosure.
2. **Trust Signals First** — confidence scores, calibration indicators, and audit chain status are always above the fold.
3. **Action in Context** — approval, rejection, annotation, and escalation happen in the same view as the data. No modal-first workflows.
4. **Immutable Trace** — every decision has a visible, clickable audit trail. Users must always be able to answer "why did this happen?"

---

## 2. COLOR SYSTEM

### Semantic Palette (CSS Custom Properties)

```css
:root {
  /* --- Base Surfaces --- */
  --color-bg-primary:        #0D0E12;   /* Main canvas — near-black */
  --color-bg-secondary:      #13151C;   /* Sidebar, panels */
  --color-bg-tertiary:       #1A1D27;   /* Cards, table rows */
  --color-bg-elevated:       #21253A;   /* Modals, popovers, dropdowns */

  /* --- Borders --- */
  --color-border-default:    #2A2E45;   /* Subtle separators */
  --color-border-strong:     #3D4260;   /* Active panels, focus rings */

  /* --- Brand Accent — Electric Indigo --- */
  --color-accent:            #6C63FF;   /* Primary CTA, active states */
  --color-accent-hover:      #7B74FF;
  --color-accent-muted:      #6C63FF22; /* Chip backgrounds, hover fills */
  --color-accent-glow:       #6C63FF44; /* Focus ring glow */

  /* --- Semantic Status --- */
  --color-success:           #22D3A0;   /* Approved, healthy, compliant */
  --color-success-bg:        #22D3A015;
  --color-warning:           #F5A623;   /* Low confidence, pending review */
  --color-warning-bg:        #F5A62315;
  --color-danger:            #FF4D6A;   /* Violation, rejected, high risk */
  --color-danger-bg:         #FF4D6A15;
  --color-neutral:           #8B93B0;   /* No decision, unknown */
  --color-neutral-bg:        #8B93B015;

  /* --- Confidence Signal Colors (XAI-specific) --- */
  --color-confidence-high:   #22D3A0;   /* ≥ 0.80 */
  --color-confidence-mid:    #F5A623;   /* 0.20–0.79 */
  --color-confidence-low:    #FF4D6A;   /* < 0.20 */

  /* --- Text --- */
  --color-text-primary:      #E8EAF6;   /* Headings, labels */
  --color-text-secondary:    #8B93B0;   /* Supporting text, metadata */
  --color-text-disabled:     #4A5070;
  --color-text-inverse:      #0D0E12;   /* On accent buttons */

  /* --- Saliency Heatmap Overlay --- */
  --color-heatmap-high:      rgba(255, 77, 106, 0.75);
  --color-heatmap-mid:       rgba(245, 166, 35, 0.55);
  --color-heatmap-low:       rgba(34, 211, 160, 0.30);
}
```

### Light Theme Overrides

```css
[data-theme="light"] {
  --color-bg-primary:        #F5F6FA;
  --color-bg-secondary:      #FFFFFF;
  --color-bg-tertiary:       #ECEEF5;
  --color-bg-elevated:       #FFFFFF;
  --color-border-default:    #DDE0ED;
  --color-border-strong:     #B8BCCC;
  --color-text-primary:      #12152A;
  --color-text-secondary:    #5A6080;
  --color-text-disabled:     #A0A8C0;
}
```

### High-Contrast Override (Accessibility)

```css
[data-theme="high-contrast"] {
  --color-bg-primary:        #000000;
  --color-bg-secondary:      #0A0A0A;
  --color-accent:            #A09AFF;
  --color-border-default:    #FFFFFF44;
  --color-text-primary:      #FFFFFF;
  --color-text-secondary:    #CCCCCC;
}
```

---

## 3. TYPOGRAPHY

```css
/* --- Font Stack --- */
--font-sans:  "Inter", "Geist", system-ui, -apple-system, sans-serif;
--font-mono:  "JetBrains Mono", "Fira Code", "Consolas", monospace;

/* --- Scale (rem, base 16px) --- */
--text-xs:    0.75rem;   /* 12px — badges, timestamps, helper text */
--text-sm:    0.8125rem; /* 13px — table cells, secondary labels */
--text-base:  0.9375rem; /* 15px — body copy, form fields */
--text-md:    1.0625rem; /* 17px — card titles, section headings */
--text-lg:    1.25rem;   /* 20px — page subtitles */
--text-xl:    1.5rem;    /* 24px — page titles */
--text-2xl:   2rem;      /* 32px — metric values, hero numbers */

/* --- Weight --- */
--font-normal:  400;
--font-medium:  500;
--font-semibold: 600;

/* --- Line Height --- */
--leading-tight:  1.3;
--leading-normal: 1.6;
--leading-loose:  1.8;

/* --- Letter Spacing --- */
--tracking-tight:  -0.02em;  /* Used on metric values, large headings */
--tracking-normal:  0em;
--tracking-wide:    0.06em;  /* Used on ALL-CAPS labels, status chips */
```

**Rules:**
- All metric/KPI numbers: `--text-2xl`, `--font-semibold`, `--tracking-tight`
- ALL-CAPS status labels: `--text-xs`, `--font-medium`, `--tracking-wide`
- Code/hash values (audit IDs, tx hashes): `--font-mono`, `--text-sm`
- Never mix more than 2 font weights on a single card

---

## 4. SPACING & LAYOUT

```css
/* --- Spacing Scale --- */
--space-1:  4px;
--space-2:  8px;
--space-3:  12px;
--space-4:  16px;
--space-5:  20px;
--space-6:  24px;
--space-8:  32px;
--space-10: 40px;
--space-12: 48px;
--space-16: 64px;

/* --- Border Radius --- */
--radius-sm:  4px;   /* Badges, chips */
--radius-md:  8px;   /* Buttons, inputs, table rows */
--radius-lg:  12px;  /* Cards, panels */
--radius-xl:  16px;  /* Modals, drawers */
--radius-full: 9999px; /* Pills, avatars */

/* --- Elevation (box-shadow) --- */
--shadow-sm:  0 1px 3px rgba(0,0,0,0.4);
--shadow-md:  0 4px 16px rgba(0,0,0,0.5);
--shadow-lg:  0 12px 40px rgba(0,0,0,0.6);
--shadow-glow: 0 0 0 2px var(--color-accent-glow);
```

### Global Layout Grid

```
┌─────────────────────────────────────────────────────────┐
│  TOP NAV (56px fixed)  — Logo | Breadcrumb | Actions    │
├──────────┬──────────────────────────────────────────────┤
│ SIDEBAR  │  MAIN CONTENT AREA                           │
│ 240px    │  max-width: 1440px, padding: 0 32px          │
│ (collap- │                                              │
│ sible to │  ┌────────────────┬───────────────────────┐  │
│ 64px)    │  │  PRIMARY PANE  │  CONTEXT PANEL (opt.) │  │
│          │  │  flex: 1       │  width: 380px          │  │
│          │  │                │  (slide-in)            │  │
│          │  └────────────────┴───────────────────────┘  │
└──────────┴──────────────────────────────────────────────┘
```

**Rule:** Context Panel (right side) is always a slide-in, never a route change. Clicking an audit item, asset, or task opens the panel. The main list never loses state.

---

## 5. COMPONENT LIBRARY

### 5.1 Confidence Badge

The most-used component in OmniAegis. Always pair with a numeric value.

```jsx
// Usage: <ConfidenceBadge value={0.87} />
// Renders: ● 87%  (color mapped to threshold)
```

**Rules:**
- High (≥0.80): `--color-confidence-high`, filled dot
- Mid (0.20–0.79): `--color-confidence-mid`, half-dot
- Low (<0.20): `--color-confidence-low`, empty dot + pulse animation
- Always show raw decimal rounded to 1dp next to dot
- Never use text alone ("High" / "Low") — always show the number

### 5.2 Status Chip

```jsx
// <StatusChip status="approved" | "rejected" | "pending" | "flagged" | "anchored" />
```

| Status | Color | Icon |
|---|---|---|
| `approved` | `--color-success` | ✓ |
| `rejected` | `--color-danger` | ✗ |
| `pending` | `--color-warning` | ⏳ |
| `flagged` | `--color-danger` | ⚑ |
| `anchored` | `--color-accent` | ⛓ (on-chain) |
| `reviewing` | `--color-neutral` | ◌ |

Background: always `{status-color}15` (15% opacity fill).

### 5.3 Data Table

- Row height: 44px (comfortable density)
- Sticky header with `position: sticky; top: 0`
- Alternating row fill: `--color-bg-tertiary` on odd rows
- Sortable columns: show sort indicator on hover for all; active column always shows direction
- Inline row actions appear on `:hover` — never shown by default (reduces visual noise)
- Multi-select: left checkbox column, bulk action bar slides up from bottom when rows selected
- Server-side pagination: `[← Prev] [1] [2] ... [N] [Next →]` — always show total count

### 5.4 Audit Trail Entry

```
┌─────────────────────────────────────────────────────────┐
│ ⛓  Anchored          AUDIT-2024-08-14-001              │
│ ─────────────────────────────────────────────────────── │
│ Asset ID   img_47f3a2   Decision   FLAGGED              │
│ Model ver  v2.3.1       Confidence 0.23 ●               │
│ Policy     ContentV3    Timestamp  2024-08-14 09:42 UTC │
│ TX Hash    0x4f2...c9a  [View on-chain ↗]              │
│ ─────────────────────────────────────────────────────── │
│ [Download Evidence Pack]   [Export JSON]   [Share Link] │
└─────────────────────────────────────────────────────────┘
```

- TX Hash always in `--font-mono`, truncated `0x4f2...c9a` with copy-on-click
- "View on-chain" opens in new tab — never in-app
- "Download Evidence Pack" generates a signed ZIP (PDF + JSON + merkle proof)

### 5.5 XAI Saliency Viewer

```
┌────────────────────────────────────────────────────────┐
│  [Original]  [Saliency]  [Overlay]  [Neighbors]        │
│  ──────────────────────────────────────────────────    │
│  ┌──────────────────┐   Saliency Regions               │
│  │                  │   1. Region A  contrib: +0.41 ██ │
│  │   [IMAGE]        │   2. Region B  contrib: +0.28 █▌ │
│  │   + HEATMAP      │   3. Region C  contrib: -0.12 ▌  │
│  │   OVERLAY        │                                  │
│  └──────────────────┘   Attribution Method             │
│  Opacity ●──────○       ● Integrated Gradients         │
│                         ○ SHAP KernelExplainer         │
│  [Export PNG]  [Export Regions JSON]                   │
└────────────────────────────────────────────────────────┘
```

**Rules:**
- Tabs switch view mode — no page navigation
- Opacity slider is a real-time overlay control (no re-fetch)
- Heatmap is CSS `mix-blend-mode: multiply` on dark; `screen` on light
- Contribution bars use signed colors: positive = `--color-success`, negative = `--color-danger`
- Neighbor grid shows 6 closest assets in a 3×2 grid with distance labels

### 5.6 HITL Task Card

```
┌────────────────────────────────────────────────────────┐
│  TASK #1847           [img]  Assigned to you  ● URGENT │
│  ─────────────────────────────────────────────────     │
│  Asset: img_47f3a2    Confidence: 0.23 ●               │
│  Policy: ContentV3    Model: v2.3.1                    │
│  ─────────────────────────────────────────────────     │
│  Context  [XAI ↗]  [Original ↗]  [Similar Cases ↗]   │
│  ─────────────────────────────────────────────────     │
│  Annotator Note: ________________________________       │
│                                                        │
│  [✗ Reject]                          [✓ Approve]      │
└────────────────────────────────────────────────────────┘
```

**Rules:**
- Reject button: left-aligned, `--color-danger` border, no fill by default
- Approve button: right-aligned, `--color-success` fill
- Both require a note if confidence < 0.40 (field auto-focuses)
- "URGENT" badge pulses if task is > 24h old and unreviewed
- Full keyboard support: `A` = Approve, `R` = Reject, `N` = focus note, `→` = next task

### 5.7 UMAP / Scatter Plot

- Zoomable & pannable (use D3 zoom or react-zoom-pan-pinch)
- Point size: 4px default, 8px on hover, 12px when selected
- Color encoding: use `--color-confidence-*` scale by default; allow toggle to color-by-label
- Selected point: white ring + glow (`--shadow-glow`)
- Cohort selection: lasso tool (hold Shift + drag)
- Right panel auto-opens with cohort summary when ≥2 points selected
- Loading state: skeleton of ~200 grey dots, fade in real points

### 5.8 Navigation Sidebar

```
● OmniAegis                           [collapse]
─────────────────────────────────────
  Overview
  ─ Ingest Explorer
  ─ Model Monitor
  ─ XAI Viewer
  ─ Audit Console                 [3]  ← badge = unanchored
  ─ HITL Board                   [12] ← badge = pending tasks
  ─ Policy Registry
─────────────────────────────────────
  Admin & Settings
  ─ Model Registry
  ─ CI Gate
  ─ Team & Access
─────────────────────────────────────
  [?] Docs   [🌙] Theme   [@] Profile
```

**Rules:**
- Active item: `--color-accent` left border (3px), `--color-accent-muted` background
- Badge counts update via WebSocket — no page refresh needed
- Collapsed state (64px): show icons only, tooltips on hover
- Never hide HITL Board or Audit Console badges in collapsed state — they are always visible

---

## 6. PAGE-BY-PAGE SPECIFICATIONS

### 6.1 Overview / Home

**Layout:** 4-col metric strip → 2-col chart row → recent activity table  
**Stream principle:** Auto-refresh every 30s. Changed metrics animate (number count-up). No full-page reload.

Key metrics strip (always visible):
```
[ Ingested Today ]  [ Decisions Made ]  [ HITL Queue Depth ]  [ Privacy Budget Remaining ]
     14,302               9,847                  12                     DP ε: 0.73 / 1.0
```

**PM rule:** Privacy budget gauge is a donut chart — when ε usage > 80%, it turns `--color-warning`. At 100%, it turns `--color-danger` and triggers a banner: "Privacy budget exhausted — model retraining required."

### 6.2 Ingest Explorer

**Layout:** Filter sidebar (left 280px) + item grid/list (right)  
**Stream principle:** Infinite scroll, not pagination. New items slide in from top if real-time ingest is active.

- Toggle between Grid (media preview cards) and List (dense table)
- Filter sidebar: Media type, Confidence range (range slider), Date range, Source, Status
- Each card: thumbnail + asset ID + confidence badge + status chip + "Quick XAI" hover action
- Clicking a card: opens Context Panel (not new page) with full metadata + XAI preview

### 6.3 Model Monitor / Drift

**Layout:** Top KPI row → 2-col: UMAP (left) + drift timeline (right)

- UMAP updates on model version select
- Drift timeline: line chart, x-axis = time, y-axis = accuracy/ECE. Vertical dashed line = model swap events
- "Model Swap" button in top-right triggers a confirmation modal with A/B comparison table

### 6.4 XAI Viewer

**Layout:** Full-width media viewer + right panel (saliency breakdown)

- Breadcrumb: `Audit Console > AUDIT-001 > XAI Viewer`
- Source of truth: users arrive here from HITL task or audit record — always carry context
- No "search for asset" on this page — it is always invoked with a specific asset ID

### 6.5 Audit Console

**Layout:** Filter bar → sortable table → context panel (slide-in on row click)

**This is the highest-priority page.** PM rule: if a user can do only one thing in OmniAegis, it is audit review.

- Default sort: most recent first, unanchored items float to top
- Row expand: inline evidence preview (no panel open needed for quick scan)
- Bulk anchor: select multiple unanchored audits → "Anchor Selected" → batch smart-contract tx
- Evidence download: always one click from row context

### 6.6 HITL Board

**Layout:** Kanban-style columns OR list view (user preference, persisted in localStorage)

Columns: `Assigned to Me` → `In Review` → `Conflict` → `Resolved`

- Task card drag: move between columns (updates status via API)
- "Conflict" column: shows tasks with ≥2 conflicting annotations — requires supervisor resolution
- Keyboard shortcut bar (always visible, bottom): `[A] Approve  [R] Reject  [N] Note  [→] Next`

### 6.7 Admin & Settings

**Layout:** Left menu tabs → right content area

Tabs: Model Registry | CI Gate | Uploads | Team & Access | Audit Policies | API Keys

- Model Registry: table of versions with accuracy, ECE, active/inactive toggle, "Set as Active" CTA
- CI Gate: confidence threshold sliders with live preview of how many past decisions would change

---

## 7. INTERACTION PATTERNS

### Real-Time Updates
- Use WebSocket or SSE for HITL queue count, ingest progress, CI gate status
- Changed values: animate with a 300ms count-up or fade transition
- New items in lists: slide-in from top, highlighted for 3s then normalize

### Loading States
- Skeleton screens for all data-heavy views (tables, UMAP, saliency)
- Never show a blank page — always skeleton first
- Long operations (batch anchor, model swap): use inline progress bar in the triggering button

### Empty States
- Never show "No data" — always explain why and what to do:
  - HITL Board empty: "No tasks in queue. The model is operating with high confidence."
  - Audit Console empty: "All audits are anchored and up to date. ✓"

### Confirmation Patterns
- Destructive actions (reject, model rollback): require explicit confirmation chip ("Type 'CONFIRM' to proceed") — not just a dialog OK
- Anchor-to-chain: show estimated gas fee + TX preview before confirming
- Never auto-submit on keyboard shortcut for Reject — always pause 500ms with "Press R again to confirm"

### Error Handling
- API errors: toast notification (bottom-right), `--color-danger`, with error code + "Copy error ID" button
- Recoverable errors: inline in the affected component, not a full-page error
- Network offline: persistent banner at top of page, not a toast

---

## 8. MOTION & ANIMATION

```css
/* --- Easing --- */
--ease-out:      cubic-bezier(0.0, 0.0, 0.2, 1.0);
--ease-in-out:   cubic-bezier(0.4, 0.0, 0.2, 1.0);
--ease-spring:   cubic-bezier(0.34, 1.56, 0.64, 1.0);

/* --- Duration --- */
--duration-fast:    100ms;   /* Hover fills, badge updates */
--duration-normal:  200ms;   /* Panel open/close, tab switch */
--duration-slow:    350ms;   /* Page transitions, modal appear */
--duration-crawl:   600ms;   /* Count-up animations, chart draw */
```

**Rules:**
- Panel slide-in: `transform: translateX(100%) → translateX(0)`, `--duration-normal`, `--ease-out`
- Modal: `opacity: 0 → 1` + `transform: scale(0.96) → scale(1)`, `--duration-slow`
- HITL task approval: checkmark draws in SVG stroke, `--duration-slow`, `--ease-spring`
- Confidence badge low-confidence pulse: `@keyframes pulse` at 2s interval, do NOT repeat on high confidence
- Respect `prefers-reduced-motion`: all animations disable, transitions ≤ 100ms

---

## 9. ACCESSIBILITY (WCAG AA MINIMUM)

- All interactive elements: focus ring = `box-shadow: var(--shadow-glow)`, 2px offset
- Color is never the only differentiator — always add icon or label (e.g., status chips have icons)
- Heatmap overlays: include a text alternative panel for color-blind users
- All modals: `role="dialog"`, `aria-modal="true"`, focus trap, `Escape` to dismiss
- HITL annotation canvas: keyboard mode must allow bounding box entry via coordinate inputs
- Saliency maps: provide a text list of top-3 contributing regions as ARIA live region
- Minimum touch target: 44×44px (mobile/tablet support for HITL field reviewers)
- Charts: all data available in a summary table accessible via keyboard

---

## 10. TAILWIND CONFIG EXTENSION

```js
// tailwind.config.ts — extend section
module.exports = {
  darkMode: ['class', '[data-theme="dark"]'],
  theme: {
    extend: {
      colors: {
        accent: {
          DEFAULT: '#6C63FF',
          hover:   '#7B74FF',
          muted:   'rgba(108, 99, 255, 0.13)',
        },
        surface: {
          primary:   '#0D0E12',
          secondary: '#13151C',
          tertiary:  '#1A1D27',
          elevated:  '#21253A',
        },
        status: {
          success: '#22D3A0',
          warning: '#F5A623',
          danger:  '#FF4D6A',
          neutral: '#8B93B0',
        },
      },
      fontFamily: {
        sans: ['Inter', 'Geist', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      fontSize: {
        '2xs': ['0.625rem', { lineHeight: '1rem' }],
      },
      boxShadow: {
        glow: '0 0 0 2px rgba(108, 99, 255, 0.27)',
      },
      transitionTimingFunction: {
        spring: 'cubic-bezier(0.34, 1.56, 0.64, 1.0)',
      },
    },
  },
};
```

---

## 11. KEY UX IMPROVEMENTS FROM PM ANALYSIS

These are specific improvements over the current codebase's UX gaps:

### 11.1 Confidence Score Visibility (CRITICAL)
**Current gap:** Confidence is buried in detail views.  
**Fix:** Confidence badge appears on every list row, every card, every task. It is the first piece of information users see.

### 11.2 Audit Trail Fragmentation (CRITICAL)  
**Current gap:** Audit records and smart-contract evidence are separate concerns in the UI.  
**Fix:** Every audit row has a single "Anchored ⛓" or "Unanchored ○" indicator. One click anchors it. The TX hash appears inline in the same row after anchoring.

### 11.3 HITL Context Loss (HIGH)
**Current gap:** HITL reviewers lose context when switching between tasks.  
**Fix:** The HITL Board uses a persistent split view — task list (left) + task detail (right). No page navigation between tasks. Keyboard navigation (→ ←) moves through the list.

### 11.4 XAI Discoverability (HIGH)
**Current gap:** XAI is a separate page requiring navigation.  
**Fix:** Every asset card and every audit row has a "Quick XAI" hover action that opens a popover with the top-3 saliency regions inline. Full XAI view opens in Context Panel, not a new route.

### 11.5 Real-Time Feedback Gaps (MEDIUM)
**Current gap:** Users must refresh to see batch job results.  
**Fix:** All long-running operations (batch ingest, FL round, model swap) show a persistent progress indicator in the sidebar below the relevant nav item. Completing operations trigger an in-app notification, not just a Prometheus metric.

### 11.6 Privacy Budget is Invisible (MEDIUM)
**Current gap:** DP epsilon is only visible in Grafana.  
**Fix:** Privacy budget gauge lives in the Overview page and in the Admin sidebar footer (always visible, collapsed to a small bar). Engineers never need to open Grafana for a quick health check.

---

## 12. RECOMMENDED DESIGN SYSTEMS FROM GETDESIGN.MD

For your Copilot/Cursor agent, use one of these as the base and layer OmniAegis tokens on top:

### Primary Recommendation: **Linear** + **Sentry** (hybrid)
```bash
npx getdesign@latest add linear.app
npx getdesign@latest add sentry
```

**Why Linear:** Ultra-minimal, precise, sidebar navigation, data-dense list views, keyboard-first interactions — identical structure to OmniAegis.

**Why Sentry:** Dark dashboard aesthetic, pink-purple accent (remap to `--color-accent: #6C63FF`), data-dense tables, error/event monitoring patterns map directly to audit/alert flows.

**How to use both:** Let Linear govern global layout, sidebar, and spacing. Let Sentry govern the table patterns, status badges, and error/alert color semantics.

### Secondary Consideration: **PostHog**
```bash
npx getdesign@latest add posthog
```
Use for the UMAP/analytics visualization patterns — PostHog has strong precedent for interactive data exploration UIs.

---

## 13. FILE STRUCTURE (FRONTEND)

```
OmniAegis-Frontend-main/
├── DESIGN.md                     ← this file
├── tailwind.config.ts            ← extend with tokens from Section 10
├── src/
│   ├── styles/
│   │   ├── globals.css           ← CSS custom properties from Section 2
│   │   └── tokens.css            ← imported in globals.css
│   ├── components/
│   │   ├── ui/
│   │   │   ├── ConfidenceBadge.tsx
│   │   │   ├── StatusChip.tsx
│   │   │   ├── AuditTrailEntry.tsx
│   │   │   └── DataTable.tsx
│   │   ├── xai/
│   │   │   ├── SaliencyViewer.tsx
│   │   │   ├── UMAPPlot.tsx
│   │   │   └── NeighborGrid.tsx
│   │   ├── hitl/
│   │   │   ├── TaskCard.tsx
│   │   │   ├── TaskBoard.tsx
│   │   │   └── AnnotationCanvas.tsx
│   │   └── layout/
│   │       ├── TopNav.tsx
│   │       ├── Sidebar.tsx
│   │       └── ContextPanel.tsx
│   └── pages/ (or app/)
│       ├── overview/
│       ├── ingest/
│       ├── monitor/
│       ├── xai/
│       ├── audit/
│       ├── hitl/
│       └── admin/
```

---

## 14. AGENT PROMPT TEMPLATE

When using this DESIGN.md with Copilot, Cursor, or Claude Code, prepend every UI prompt with:

```
Follow DESIGN.md at the project root for all design decisions.
Use CSS custom properties defined in Section 2 for all colors.
Apply the spacing scale from Section 4. Do not hardcode color values.
Component being built: [name from Section 5]
Page context: [page from Section 6]
```

---

*Generated for OmniAegis / SentinelAgent — AI Audit, Monitoring & Explainability Platform*  
*Thinking: Product Manager perspective — stream-like experience, trust signals first, action in context.*