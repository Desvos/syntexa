# Feature Specification: Frontend MUI Refactor

**Short Name**: frontend-mui-refactor
**Status**: Draft
**Created**: 2026-04-15
**Author**: antoniodevivo

## Overview

This specification outlines the complete migration of the Syntexa dashboard frontend from its current vanilla CSS implementation to Material-UI (MUI) version 6. The refactor will replace ad-hoc styling with a comprehensive design system, providing a consistent, accessible, and professional user interface while maintaining full functional parity with the existing application.

**Current State**: The frontend uses vanilla CSS classes (e.g., `className="login-form-container"`) with component-scoped styles, resulting in inconsistent spacing, lack of design tokens, and limited component reusability.

**Target State**: A fully MUI-based application using Material Design principles, with theme customization, pre-built components, and professional-grade accessibility.

**Note**: This specification is drafted for future development and should be prioritized based on product roadmap needs.

## Motivation

| Current Pain Point | MUI Solution |
|--------------------|--------------|
| Inconsistent spacing and colors across pages | Centralized theme with design tokens |
| Manual implementation of dialogs, tables, forms | Rich component library out of the box |
| No responsive breakpoint system | Built-in responsive Grid and breakpoints |
| Accessibility requires manual effort | WCAG 2.1 compliant components by default |
| No dark mode support | Built-in theme switching |
| Limited form validation UI | FormControl with validation states |
| Manual icon imports and sizing | Integrated @mui/icons-material |
| No loading states or skeletons | Skeleton, CircularProgress, LinearProgress |
| Table sorting/filtering manual | DataGrid component with built-in features |

## User Scenarios & Testing

### Primary Scenario

**As a** platform administrator,
**I want** to interact with a consistent, modern, and accessible dashboard interface,
**So that** I can efficiently manage agents, compositions, and settings without visual distractions or confusing interactions.

**Steps**:
1. Administrator opens the dashboard
2. Login page displays with MUI TextField and Button components
3. After authentication, navigation drawer provides consistent wayfinding
4. Each page uses standardized MUI Cards, Tables, and Forms
5. Interactive elements show proper hover, focus, and active states
6. Forms validate inline with MUI error states
7. Loading states show MUI Skeletons or CircularProgress

### Migration Scenarios

| Scenario                     | Condition                            | Expected Outcome                         |
|------------------------------|--------------------------------------|------------------------------------------|
| Component audit              | Inventory all existing components    | List of components with migration priority |
| Theme configuration            | Set up MUI theme provider            | Custom primary/secondary colors match brand |
| Incremental migration          | Refactor one page at a time          | No breaking changes, mixed UI acceptable briefly |
| Form refactor                  | Replace inputs with TextField        | Validation, labels, hints per MUI patterns |
| Table refactor                 | Replace custom tables with DataGrid  | Sorting, filtering, pagination built-in |
| Dialog refactor                | Replace custom modals with MUI       | Consistent backdrops and animations |
| Icon migration                 | Replace SVG/emoji with MUI icons     | Consistent sizing and accessibility |
| Responsive verification        | Test on tablet/mobile viewports      | Layout adapts using MUI Grid system |

### Edge Cases

| Edge Case                    | Trigger                            | Handling                                |
|------------------------------|------------------------------------|-----------------------------------------|
| Custom CSS needed            | MUI component doesn't match design | Use sx prop or styled() for overrides |
| Performance degradation        | MUI bundle too large               | Implement tree-shaking and lazy loading |
| Theme flash on load            | Dark mode preference               | Store theme in localStorage, apply before render |
| Prop type mismatch             | Migration incomplete               | TypeScript strict mode catches at build |
| Nested component styling         | Complex overrides needed           | Document pattern in STYLEGUIDE.md |
| Bundle size increase             | All MUI components imported          | Use path imports, not top-level |

## Functional Requirements

### FR-1: MUI Theme Setup

**Priority**: Must
**Description**: The application MUST be wrapped with MUI ThemeProvider configured with custom brand colors, typography, and spacing.

**Acceptance Criteria**:
- [ ] ThemeProvider wraps entire application at root level
- [ ] Custom theme defines primary and secondary colors matching Syntexa brand
- [ ] Typography scale configured for headings, body, captions
- [ ] Spacing multiplier set (default 8px base)
- [ ] Breakpoints defined for mobile, tablet, desktop
- [ ] CssBaseline component included for CSS reset

### FR-2: Component Inventory & Priority

**Priority**: Must
**Description**: An audit MUST be completed categorizing all existing components by migration priority and effort.

**Acceptance Criteria**:
- [ ] Document created listing all components in `/src/components/` and `/src/pages/`
- [ ] Each component rated: Critical (user-facing), Medium (admin), Low (internal)
- [ ] Migration order established: Layout → Forms → Tables → Misc
- [ ] Dependency graph showing which pages share components
- [ ] Estimated effort per component (hours)

### FR-3: Layout Components Migration

**Priority**: Must
**Description**: Application shell components (navigation, header, layout) MUST be migrated to MUI first to establish visual foundation.

**Acceptance Criteria**:
- [ ] AppBar component for header with logo and user menu
- [ ] Drawer component for navigation sidebar
- [ ] Container and Box used for page layouts
- [ ] Grid system replaces custom layout CSS
- [ ] Responsive behavior: drawer collapses to hamburger on mobile

### FR-4: Form Components Migration

**Priority**: Must
**Description**: All form inputs MUST be replaced with MUI FormControl, TextField, Select, Checkbox, and Button components.

**Acceptance Criteria**:
- [ ] TextField replaces all `<input>` elements
- [ ] Select replaces all `<select>` elements
- [ ] FormLabel and InputLabel used for accessibility
- [ ] FormHelperText for validation messages
- [ ] Button replaces all `<button>` with variant hierarchy (contained/outlined/text)
- [ ] Loading state shows Button with CircularProgress

### FR-5: Data Display Components

**Priority**: Must
**Description**: Tables, cards, and lists MUST use MUI DataGrid, Card, and List components.

**Acceptance Criteria**:
- [ ] DataGrid replaces RolesTable and CompositionsTable
- [ ] Columns configurable with sorting and filtering
- [ ] Card replaces custom panel/card styles
- [ ] Chip component used for status badges and tags
- [ ] Avatar component for user representation
- [ ] Tooltip wraps icon buttons for clarity

### FR-6: Feedback Components

**Priority**: Must
**Description**: Loading states, alerts, and notifications MUST use MUI Skeleton, Alert, Snackbar, and Dialog components.

**Acceptance Criteria**:
- [ ] Skeleton shown during initial data load
- [ ] CircularProgress for button loading states
- [ ] Alert used for inline error/success messages
- [ ] Snackbar for transient notifications (auto-hide)
- [ ] Dialog replaces custom modals for confirmations
- [ ] Backdrop used for full-screen loading states

### FR-7: Icon Migration

**Priority**: Should
**Description**: All icons SHOULD be replaced with @mui/icons-material equivalents.

**Acceptance Criteria**:
- [ ] IconButton wraps icons for clickable actions
- [ ] Navigation icons: Dashboard, People, Settings, etc.
- [ ] Action icons: Edit, Delete, Add, Refresh
- - [ ] Status icons: CheckCircle, Error, Warning, Info
- [ ] Custom SVG icons only where no Material icon exists

### FR-8: Theme Customization

**Priority**: Should
**Description**: Administrators SHOULD be able to toggle between light and dark themes.

**Acceptance Criteria**:
- [ ] Theme toggle button in user menu
- [ ] Preference persisted to localStorage
- [ ] System preference detection as default
- [ ] No flash on theme change (transition animation)
- [ ] All components respect theme (no hardcoded colors)

### FR-9: Responsive Design

**Priority**: Should
**Description**: All pages SHOULD be fully responsive using MUI's breakpoint system.

**Acceptance Criteria**:
- [ ] Mobile: single column, drawer as overlay
- [ ] Tablet: two-column where appropriate
- [ ] Desktop: full layout with persistent drawer
- [ ] DataGrid horizontal scroll on small screens
- [ ] Breakpoints tested: xs, sm, md, lg thresholds

### FR-10: Accessibility Compliance

**Priority**: Must
**Description**: The refactored application MUST maintain or improve accessibility compliance.

**Acceptance Criteria**:
- [ ] All interactive elements keyboard navigable
- [ ] Focus indicators visible and consistent
- [ ] ARIA labels on icon buttons
- [ ] Color contrast meets WCAG AA (4.5:1)
- [ ] Screen reader testing passes
- [ ] No axe-core violations in CI

## Migration Plan

### Phase 1: Foundation (Week 1)
- Install MUI dependencies
- Configure ThemeProvider and CssBaseline
- Set up custom theme with brand colors
- Create component migration documentation

### Phase 2: Layout (Week 1-2)
- Migrate App shell (AppBar, Drawer)
- Refactor page layout containers
- Implement responsive Grid system
- Test navigation across viewports

### Phase 3: Core Components (Week 2-3)
- LoginForm with TextField, Button
- ProtectedRoute with Backdrop loading
- UsersTable with DataGrid
- RolesTable with DataGrid

### Phase 4: Feature Pages (Week 3-4)
- Compositions page with Card layouts
- Settings page with FormControl
- Monitor page with real-time updates
- Status displays with Chip and Alert

### Phase 5: Polish (Week 4)
- Icon migration
- Theme toggle implementation
- Animation/transitions
- Final responsive testing
- Accessibility audit

### Phase 6: Cleanup (Week 5)
- Remove old CSS files
- Deprecate unused components
- Update documentation
- Performance regression testing

## Dependency Changes

### Install
```bash
bun add @mui/material @emotion/react @emotion/styled @mui/icons-material
bun add @mui/x-data-grid
bun add -D @types/node  # if TypeScript adopted
```

### Remove (Post-Migration)
- Custom CSS files (base.css, component styles)
- Vanilla CSS className usage
- Manual SVG icon imports (if any)

## Success Criteria

| Criterion                      | Measure                           | Target           |
|-------------------------------|-----------------------------------|------------------|
| Component coverage            | % of UI using MUI components      | 100%             |
| Visual regression               | Screenshots vs. original            | Pixel-perfect intent |
| Bundle size                     | JS bundle size delta               | <50KB increase   |
| Lighthouse accessibility        | Score                              | 100              |
| Lighthouse performance          | Score                              | ≥90              |
| Build warnings                  | Deprecation/style warnings         | Zero             |
| Test pass rate                  | Existing tests                     | 100% passing     |
| Theme consistency               | Color/style audit                  | Zero hardcoded values |

## Out of Scope

- Migration to TypeScript (can be combined but separate concern)
- State management refactor (keep existing patterns)
- API client changes (keep existing fetch/axios patterns)
- Component library extraction for external use
- Custom MUI theme marketplace/sharing
- Server-side rendering (SSR) migration
- Component-level unit testing (keep existing coverage level)

## Migration Checklist

Components to migrate:
- [ ] LoginForm.jsx
- [ ] ProtectedRoute.jsx
- [ ] RolesTable.jsx
- [ ] RoleEditor.jsx
- [ ] CompositionsTable.jsx
- [ ] CompositionEditor.jsx
- [ ] UsersTable.jsx
- [ ] ConnectionStatus.jsx
- [ ] ActiveSwarms.jsx
- [ ] CompletedSwarms.jsx
- [ ] LogViewer.jsx
- [ ] HandoffTargets.jsx
- [ ] TaskTypeSelect.jsx
- [ ] RoleOrder.jsx

Pages to migrate:
- [ ] Login.jsx
- [ ] Users.jsx
- [ ] Roles.jsx
- [ ] Compositions.jsx
- [ ] Settings.jsx
- [ ] Monitor.jsx

## Constitution Compliance

| Principle           | Compliance                                                              |
|---------------------|-------------------------------------------------------------------------|
| Clarity First       | MUI provides consistent, recognizable patterns; migration documented step-by-step |
| Test-Driven         | Visual regression tests added; existing functional tests maintained |
| Modular Architecture| Components remain decoupled; MUI theme is injectable dependency |
| Security by Default | No change to security posture; MUI components follow security best practices |
