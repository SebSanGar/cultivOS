# cultivOS — Design System

> Auto-extracted by `autoagent/scripts/extract_design_system.py` for the
> Claude Design workflow (see `skills/claude-design.md`). Import this file
> (or `design-system.json`) into Claude Design so it builds + self-checks
> against the real system. Review + consolidate before treating as canon.

- **Source:** `/Users/SebSan/Documents/cultivOS/frontend/styles.css`
- **Tokens:** 105  ·  **Components:** 1032

## Color tokens

| Token | Value |
|---|---|
| `--accent` | `#16a34a` |
| `--accent-green` | `var(--brand-green)` |
| `--bg` | `#fafaf9` |
| `--bg-tertiary` | `var(--neutral-100)` |
| `--border` | `#e5e7eb` |
| `--border-color` | `var(--border)` |
| `--brand-green` | `#16a34a` |
| `--brand-green-100` | `#dcfce7` |
| `--brand-green-50` | `#f0fdf4` |
| `--brand-green-600` | `#16a34a` |
| `--brand-green-800` | `#166534` |
| `--brand-green-900` | `#14532d` |
| `--brand-green-dark` | `#14532d` |
| `--brand-green-light` | `#dcfce7` |
| `--bronze` | `#b45309` |
| `--card-bg` | `var(--surface)` |
| `--card-surface` | `var(--surface)` |
| `--color-danger` | `#dc2626` |
| `--color-danger-dark` | `#991b1b` |
| `--color-danger-light` | `#fee2e2` |
| `--color-info` | `#2563eb` |
| `--color-info-light` | `#dbeafe` |
| `--color-success` | `#16a34a` |
| `--color-success-dark` | `#166534` |
| `--color-success-light` | `#dcfce7` |
| `--color-warning` | `#d97706` |
| `--color-warning-dark` | `#92400e` |
| `--color-warning-light` | `#fef3c7` |
| `--focus-ring` | `0 0 0 2px rgba(22, 163, 74, 0.2)` |
| `--gold` | `#d97706` |
| `--green` | `var(--brand-green)` |
| `--green-dark` | `var(--brand-green-dark)` |
| `--green-light` | `var(--brand-green-light)` |
| `--green-mid` | `#4ade80` |
| `--green-soft` | `#bbf7d0` |
| `--input-bg` | `var(--surface)` |
| `--intel-bg` | `var(--bg)` |
| `--intel-border` | `var(--border)` |
| `--intel-muted` | `var(--text-muted)` |
| `--intel-surface` | `var(--surface)` |
| `--intel-text` | `var(--text)` |
| `--muted` | `var(--text-muted)` |
| `--neutral-100` | `#f5f5f4` |
| `--neutral-200` | `#e7e5e4` |
| `--neutral-300` | `#d6d3d1` |
| `--neutral-400` | `#a8a29e` |
| `--neutral-50` | `#fafaf9` |
| `--neutral-500` | `#78716c` |
| `--neutral-600` | `#57534e` |
| `--neutral-700` | `#44403c` |
| `--neutral-800` | `#292524` |
| `--neutral-900` | `#1c1917` |
| `--purple` | `#7c3aed` |
| `--silver` | `#9ca3af` |
| `--surface` | `#ffffff` |
| `--surface-2` | `var(--neutral-50)` |
| `--text` | `#1a1a1a` |
| `--text-muted` | `#6b7280` |
| `--text-primary` | `var(--text)` |
| `--text-secondary` | `var(--text-muted)` |

## Typography tokens

| Token | Value |
|---|---|
| `--font-body` | `'Inter', system-ui, -apple-system, sans-serif` |
| `--font-heading` | `'Space Grotesk', system-ui, sans-serif` |
| `--font-mono` | `'JetBrains Mono', 'SF Mono', monospace` |
| `--text-2xl` | `1.5rem` |
| `--text-3xl` | `1.875rem` |
| `--text-4xl` | `2.25rem` |
| `--text-base` | `1rem` |
| `--text-lg` | `1.125rem` |
| `--text-sm` | `0.875rem` |
| `--text-xl` | `1.25rem` |
| `--text-xs` | `0.75rem` |

## Spacing tokens

| Token | Value |
|---|---|
| `--space-1` | `0.25rem` |
| `--space-10` | `2.5rem` |
| `--space-12` | `3rem` |
| `--space-16` | `4rem` |
| `--space-2` | `0.5rem` |
| `--space-3` | `0.75rem` |
| `--space-4` | `1rem` |
| `--space-5` | `1.25rem` |
| `--space-6` | `1.5rem` |
| `--space-8` | `2rem` |

## Radius tokens

| Token | Value |
|---|---|
| `--radius` | `12px` |
| `--radius-full` | `9999px` |
| `--radius-lg` | `16px` |
| `--radius-sm` | `6px` |
| `--radius-xl` | `24px` |

## Shadow tokens

| Token | Value |
|---|---|
| `--shadow` | `0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06)` |
| `--shadow-lg` | `0 10px 15px rgba(0,0,0,0.1), 0 4px 6px rgba(0,0,0,0.05)` |
| `--shadow-md` | `0 4px 6px rgba(0,0,0,0.07), 0 2px 4px rgba(0,0,0,0.06)` |
| `--shadow-sm` | `0 1px 2px rgba(0,0,0,0.05)` |
| `--shadow-xl` | `0 20px 25px rgba(0,0,0,0.1), 0 8px 10px rgba(0,0,0,0.04)` |

## Motion tokens

| Token | Value |
|---|---|
| `--duration-fast` | `150ms` |
| `--duration-normal` | `250ms` |
| `--duration-slow` | `400ms` |
| `--ease-in-out` | `cubic-bezier(0.65, 0, 0.35, 1)` |
| `--ease-out` | `cubic-bezier(0.16, 1, 0.3, 1)` |
| `--ease-spring` | `cubic-bezier(0.34, 1.56, 0.64, 1)` |

## Other tokens

| Token | Value |
|---|---|
| `--amber` | `var(--color-warning)` |
| `--blue` | `var(--color-info)` |
| `--blue-light` | `var(--color-info-light)` |
| `--card` | `var(--surface)` |
| `--red` | `var(--color-danger)` |
| `--red-light` | `var(--color-danger-light)` |
| `--yellow` | `var(--color-warning)` |
| `--yellow-light` | `var(--color-warning-light)` |

## Drift signal — class-prefix families (review for consolidation)

| Prefix | Variants |
|---|---|
| `treatment-*` | 46 |
| `intel-*` | 44 |
| `seasonal-*` | 41 |
| `alert-*` | 38 |
| `campo-*` | 30 |
| `fusion-*` | 30 |
| `soil-*` | 29 |
| `recs-*` | 29 |
| `weather-*` | 28 |
| `knowledge-*` | 28 |
| `wizard-*` | 25 |
| `tl-*` | 24 |
| `mgmt-*` | 23 |
| `field-*` | 22 |
| `econ-*` | 22 |
| `impact-*` | 22 |
| `cerebro-*` | 19 |
| `notif-*` | 18 |
| `heatmap-*` | 17 |
| `nav-*` | 16 |
| `regen-*` | 16 |
| `timing-*` | 16 |
| `si-*` | 16 |
| `regional-*` | 14 |
| `growth-*` | 14 |
| `status-*` | 14 |
| `intervention-*` | 13 |
| `feedback-*` | 13 |
| `api-*` | 13 |
| `rotation-*` | 12 |
| `completeness-*` | 12 |
| `tek-*` | 12 |
| `sensor-*` | 12 |
| `tour-*` | 12 |
| `timeline-*` | 11 |
| `notification-*` | 11 |
| `compare-*` | 11 |
| `comparison-*` | 11 |
| `zone-*` | 10 |
| `disease-*` | 9 |
| `severity-*` | 9 |
| `farm-*` | 8 |
| `anomaly-*` | 8 |
| `batch-*` | 8 |
| `identify-*` | 8 |
| `summary-*` | 8 |
| `flights-*` | 8 |
| `login-*` | 8 |
| `dashboard-*` | 6 |
| `health-*` | 6 |
| `microbiome-*` | 6 |
| `payback-*` | 6 |
| `sparkline-*` | 5 |
| `forecast-*` | 5 |
| `mission-*` | 5 |
| `empty-*` | 4 |
| `urgency-*` | 4 |
| `fert-*` | 4 |
| `delta-*` | 4 |
| `owner-*` | 4 |
| `estimate-*` | 4 |
| `kpi-*` | 4 |
| `page-*` | 4 |

## Top components (by rule frequency)

| Selector | Rules |
|---|---|
| `.platform-page` | 17 |
| `.critical` | 14 |
| `.alert-check-card` | 13 |
| `.warning` | 12 |
| `.intel-body` | 11 |
| `.good` | 10 |
| `.campo-grid` | 9 |
| `.flights-table` | 9 |
| `.health-badge` | 9 |
| `.active` | 8 |
| `.campo-section` | 8 |
| `.intel-stat` | 8 |
| `.mgmt-form-group` | 8 |
| `.intel-grid` | 7 |
| `.notification-severity` | 7 |
| `.soil-form-field` | 7 |
| `.ba-swatch` | 6 |
| `.compare-sortable` | 6 |
| `.comparison-table` | 6 |
| `.heatmap-circle` | 6 |
| `.intel-panel` | 6 |
| `.login-field` | 6 |
| `.nav-farmer-tabs` | 6 |
| `.nav-inner` | 6 |
| `.stat-card` | 6 |
| `.wizard-form-group` | 6 |
| `.alert-check-card-title` | 5 |
| `.alert-check-icon` | 5 |
| `.alert-history-dot` | 5 |
| `.alert-history-type-badge` | 5 |
| `.batch-health-card` | 5 |
| `.compare-header-row` | 5 |
| `.cultivos-footer` | 5 |
| `.heatmap-dot` | 5 |
| `.nav-tab` | 5 |
| `.notif-card` | 5 |
| `.seasonal-alert-card` | 5 |
| `.seasonal-type-dot` | 5 |
| `.semaforo-dot` | 5 |
| `.wizard-progress-step` | 5 |
