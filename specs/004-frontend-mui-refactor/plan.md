# Implementation Plan: Frontend MUI Refactor

**Spec**: [spec.md](spec.md)  
**Data Model**: [data-model.md](data-model.md)  
**Research**: [research.md](research.md)  
**Status**: Draft  
**Created**: 2026-04-17  
**Author**: antoniodevivo  

---

## Plan Overview

This plan migrates the Syntexa dashboard from vanilla CSS to Material-UI (MUI) v6. The approach is **incremental by page**, allowing gradual migration without breaking functionality.

**Key Strategy**:
1. Install MUI dependencies at project root
2. Create theme infrastructure (provider, tokens)
3. Migrate layout components first (app shell)
4. Migrate pages in order: Login → Pages with forms → Pages with tables
5. Final cleanup of legacy CSS

**No Breaking Changes**: Old and new components coexist during migration.

---

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| Clarity First | ✅ Aligned | MUI provides consistent, recognizable patterns; well-documented props |
| Test-Driven | ✅ Aligned | Maintain existing test coverage, add visual regression tests |
| Modular Architecture | ✅ Aligned | Components remain isolated, theme is injectable dependency |
| Security by Default | ✅ Aligned | No security changes; MUI follows security best practices |

---

## Architecture Decisions

### AD-1: Migration Strategy - Incremental Per Page

**Context**: Need to migrate ~25 components without breaking existing functionality
**Decision**: Migrate page-by-page starting with simplest (Login), keeping old CSS during transition
**Alternatives Considered**:
- Big-bang rewrite: Too risky, hard to debug
- Component-by-component: Creates dependency issues with shared styles
**Rationale**: Each page can be tested independently; rollback is page-level; clear progress milestones

### AD-2: Import Strategy - Path Imports Only

**Context**: MUI barrel imports prevent tree-shaking, increasing bundle size significantly
**Decision**: Use path imports (`@mui/material/Button`) not barrel imports
**Alternatives Considered**:
- Barrel imports: Simpler but +200KB bundle
- Custom babel plugin for tree-shaking: Overkill for this project
**Rationale**: Path imports guarantee minimal bundle size; explicit dependencies are clearer

### AD-3: Theme Management - Context + localStorage

**Context**: Need theme customization (dark mode, brand colors) that persists
**Decision**: React Context for ThemeProvider + localStorage for persistence
**Alternatives Considered**:
- Redux: Overkill for theme state
- CSS variables only: No programmatic access for dark mode toggle
**Rationale**: Context is idiomatic React, localStorage is simple persistence, no external deps

### AD-4: Table Migration - DataGrid (Free)

**Context**: Current tables are custom-built with sorting/filtering logic
**Decision**: Replace with MUI X DataGrid (free version)
**Alternatives Considered**:
- Custom Table component: Too much work, maintenance burden
- DataGrid Pro: Paid, not needed for current features
**Rationale**: DataGrid free has pagination, sorting, row selection; matches all current table needs

### AD-5: Responsive Approach - MUI Grid System

**Context**: Current CSS uses custom media queries at various breakpoints
**Decision**: Replace with MUI Grid v2 and default breakpoints
**Alternatives Considered**:
- Keep custom queries: Doesn't leverage MUI theme system
- CSS-in-JS for queries: Less consistent than MUI Grid
**Rationale**: MUI Grid integrates with theme, provides consistent spacing, mobile-first responsive

### AD-6: Icon System - @mui/icons-material

**Context**: Project currently uses SVG or emoji icons inconsistently
**Decision**: Standardize on @mui/icons-material with IconButton wrapper
**Alternatives Considered**:
- Keep existing SVGs: Inconsistent sizing, no theme integration
- Third-party icon library: Extra dependency, less MUI integration
**Rationale**: MUI icons integrate with theme colors, have consistent sizing, Tree-shakeable

### AD-7: Form Validation - Controlled Components with MUI States

**Context**: Forms need validation display (error states, helper text)
**Decision**: Use MUI TextField with error/helperText props, controlled by form state
**Alternatives Considered**:
- Form libraries (Formik, React Hook Form): Add complexity, not necessary for simple forms
- Native validation: Doesn't match MUI design patterns
**Rationale**: MUI components have built-in validation styling; keep forms simple and maintainable

---

## Implementation Phases

### Phase 1: Foundation

**Goal**: Install MUI and set up theme infrastructure
**Requirements Covered**: FR-1, FR-2 (partial)
**Estimated Effort**: 3-4 hours

**Steps**:
1. [ ] Install MUI dependencies: `@mui/material`, `@emotion/react`, `@emotion/styled`, `@mui/icons-material`, `@mui/x-data-grid`
2. [ ] Create `dashboard/src/theme.js` with custom theme configuration
3. [ ] Create `dashboard/src/components/ThemeProvider.jsx` wrapper with dark mode support
4. [ ] Wrap App with ThemeProvider in `main.jsx`
5. [ ] Create component inventory document: `docs/components-migration.md`
6. [ ] Run build and verify no bundle size regression (>50KB)
7. [ ] Create `LoadingFallback.jsx` with MUI Skeleton for suspense

**Deliverables**:
- `dashboard/src/theme.js` - Theme configuration
- `dashboard/src/components/ThemeProvider.jsx` - Theme context provider
- `docs/components-migration.md` - Component inventory and priority
- Updated `dashboard/src/main.jsx` - Wrapped with ThemeProvider
- `dashboard/src/components/LoadingFallback.jsx` - Loading state component

**Test Strategy**:
- Manual: Verify theme loads, no console errors
- Automated: Build succeeds, bundle size < 50KB increase
- Check: Theme toggle works (even if no UI yet)

---

### Phase 2: Layout Migration

**Goal**: Migrate application shell components
**Requirements Covered**: FR-3
**Estimated Effort**: 4-5 hours

**Steps**:
1. [ ] Create `dashboard/src/components/AppLayout.jsx` with MUI AppBar, Drawer, Container
2. [ ] Migrate navigation to use MUI Drawer (persistent on desktop, temporary on mobile)
3. [ ] Create `dashboard/src/components/NavList.jsx` with List, ListItem, ListItemIcon, ListItemText
4. [ ] Update page layouts to use MUI Box/Container/Grid
5. [ ] Add responsive behavior: drawer collapses on mobile, hamburger menu
6. [ ] Create `dashboard/src/components/UserMenu.jsx` for header user actions
7. [ ] Update routing integration with new layout wrapper
8. [ ] Verify responsive behavior on xs, sm, md, lg breakpoints

**Deliverables**:
- `dashboard/src/components/AppLayout.jsx` - App shell with AppBar, Drawer
- `dashboard/src/components/NavList.jsx` - Navigation items
- `dashboard/src/components/UserMenu.jsx` - Header user menu
- Updated page components using new layout
- CSS: Remove old layout CSS classes

**Test Strategy**:
- Manual: Test navigation on mobile and desktop viewports
- Manual: Verify drawer open/close, menu interactions
- Automated: Existing routing tests pass

---

### Phase 3: Login Page Migration

**Goal**: Complete migration of Login page and form components
**Requirements Covered**: FR-4
**Estimated Effort**: 3-4 hours

**Steps**:
1. [ ] Create MUI `LoginForm.jsx` with TextField (email, password), Button
2. [ ] Add FormControl and validation states (error, helperText)
3. [ ] Add visibility toggle for password field (IconButton with Visibility icon)
4. [ ] Add loading state with CircularProgress in Button
5. [ ] Update `Login.jsx` page with MUI Card, CardContent for form container
6. [ ] Add Alert component for login error display
7. [ ] Verify form accessibility (labels, focus management)
8. [ ] Update/rewrite component tests for new implementation

**Deliverables**:
- `dashboard/src/components/LoginForm.jsx` - MUI-based login form
- Updated `dashboard/src/pages/Login.jsx` - Page wrapper with Card layout
- Component tests updated

**Test Strategy**:
- Automated: Form submission works, validation displays
- Manual: Visual appearance matches intent
- Accessibility: Keyboard navigation, focus visible

---

### Phase 4: User Management Migration

**Goal**: Migrate Users page and table to DataGrid
**Requirements Covered**: FR-4, FR-5
**Estimated Effort**: 4-5 hours

**Steps**:
1. [ ] Create new `UsersTable.jsx` using DataGrid component
2. [ ] Define columns: name, email, role, status, actions
3. [ ] Add actions column with IconButton (edit, delete)
4. [ ] Implement row selection with checkboxSelection
5. [ ] Add pagination with pageSize options [10, 25, 50]
6. [ ] Create `UserDialog.jsx` for create/edit user modals using MUI Dialog
7. [ ] Replace form inputs with MUI TextField, Select components
8. [ ] Update `Users.jsx` page with MUI layout containers
9. [ ] Add Toolbar with Button for "Add User" action

**Deliverables**:
- `dashboard/src/components/UsersTable.jsx` - DataGrid-based table
- `dashboard/src/components/UserDialog.jsx` - Create/edit modal
- Updated `dashboard/src/pages/Users.jsx` - Page layout

**Test Strategy**:
- Automated: Table renders with data, sorting works
- Manual: CRUD operations via modal
- Manual: Responsive table with horizontal scroll on mobile

---

### Phase 5: Agent Roles Migration

**Goal**: Migrate Roles page, table, and editor to MUI
**Requirements Covered**: FR-4, FR-5
**Estimated Effort**: 4-5 hours

**Steps**:
1. [ ] Create `RolesTable.jsx` with DataGrid (columns: name, model, status, actions)
2. [ ] Use Chip component for status display
3. [ ] Create `RoleEditor.jsx` with MUI form components
4. [ ] Add TextField for name with validation
5. [ ] Add Select for model/provider dropdowns
6. [ ] Add TextField (multiline) for system prompt with character counter
7. [ ] Create `HandoffTargets.jsx` with MUI Switch or Checkbox for toggles
8. [ ] Update `Roles.jsx` page with MUI Card layouts
9. [ ] Add Dialog for confirmation on delete

**Deliverables**:
- `dashboard/src/components/RolesTable.jsx` - DataGrid-based
- `dashboard/src/components/RoleEditor.jsx` - Form with validation
- `dashboard/src/components/HandoffTargets.jsx` - Multi-select with switches
- Updated `dashboard/src/pages/Roles.jsx`

**Test Strategy**:
- Automated: Form validation works, editor opens/closes
- Manual: Multi-select handoff targets interaction

---

### Phase 6: Compositions Migration

**Goal**: Migrate Swarm Compositions page
**Requirements Covered**: FR-4, FR-5
**Estimated Effort**: 3-4 hours

**Steps**:
1. [ ] Create `CompositionsTable.jsx` with DataGrid
2. [ ] Create `CompositionEditor.jsx` with form fields
3. [ ] Create `RoleOrder.jsx` drag-to-reorder using MUI List + icons (or simpler Select ordering)
4. [ ] Use Chip for displaying ordered roles in table
5. [ ] Create `TaskTypeSelect.jsx` with MUI Select
6. [ ] Update `Compositions.jsx` page
7. [ ] Add Card-based layout for viewing compositions

**Deliverables**:
- `dashboard/src/components/CompositionsTable.jsx`
- `dashboard/src/components/CompositionEditor.jsx`
- `dashboard/src/components/RoleOrder.jsx` - Drag or order control
- `dashboard/src/components/TaskTypeSelect.jsx`
- Updated `dashboard/src/pages/Compositions.jsx`

**Test Strategy**:
- Manual: Composition creation flow
- Manual: Role ordering interaction

---

### Phase 7: Settings & Monitor Migration

**Goal**: Migrate Settings and Monitor pages with feedback components
**Requirements Covered**: FR-4, FR-5, FR-6
**Estimated Effort**: 4-5 hours

**Steps**:
1. [ ] Update `Settings.jsx` with MUI form controls
2. [ ] Add Switch for boolean settings
3. [ ] Add Slider for numeric settings (polling interval)
4. [ ] Add TextField for token/config inputs
5. [ ] Create `ConnectionStatus.jsx` with MUI Alert (success/error variants)
6. [ ] Update `Monitor.jsx` with MUI Card layout
7. [ ] Create `ActiveSwarms.jsx` with DataGrid for active tasks
8. [ ] Create `CompletedSwarms.jsx` with DataGrid for history
9. [ ] Create `LogViewer.jsx` with MUI Paper + scrolling container
10. [ ] Add Skeleton loading states for data fetching

**Deliverables**:
- Updated `dashboard/src/pages/Settings.jsx`
- Updated `dashboard/src/components/ConnectionStatus.jsx`
- Updated `dashboard/src/pages/Monitor.jsx`
- `dashboard/src/components/ActiveSwarms.jsx` - With DataGrid
- `dashboard/src/components/CompletedSwarms.jsx` - With DataGrid
- Updated `dashboard/src/components/LogViewer.jsx` - With Paper styling

**Test Strategy**:
- Manual: Settings form with all control types
- Manual: Monitor page with real-time updates (if available)
- Visual: Loading states with Skeleton

---

### Phase 8: Feedback & Theme Components

**Goal**: Add comprehensive feedback components and theme toggle
**Requirements Covered**: FR-6, FR-8
**Estimated Effort**: 3-4 hours

**Steps**:
1. [ ] Create `SnackbarProvider.jsx` for app-wide notifications
2. [ ] Add Snackbar hooks for success/error messages
3. [ ] Update UserMenu with theme toggle (light/dark/system)
4. [ ] Add theme persistence to localStorage
5. [ ] Create theme transition (CssVarsProvider or CSS transition)
6. [ ] Add Backdrop component for full-screen loading states
7. [ ] Create `ErrorBoundary.jsx` with MUI Alert fallback
8. [ ] Add CircularProgress for async button states throughout

**Deliverables**:
- `dashboard/src/components/SnackbarProvider.jsx` - Global notifications
- `dashboard/src/components/ErrorBoundary.jsx` - Error display
- Updated `dashboard/src/components/UserMenu.jsx` - With theme toggle
- Updated `dashboard/src/components/ThemeProvider.jsx` - With persistence

**Test Strategy**:
- Manual: Snackbar notifications appear on actions
- Manual: Theme toggle persists across reloads
- Manual: No flash on theme change

---

### Phase 9: Icon Migration & Final Polish

**Goal**: Replace all remaining icons and finalize styling
**Requirements Covered**: FR-7, FR-9, FR-10
**Estimated Effort**: 4-5 hours

**Steps**:
1. [ ] Audit all icon usage: grep for `<svg`, emoji, `className="icon`
2. [ ] Replace with @mui/icons-material equivalents
3. [ ] IconButton for all clickable icons
4. [ ] Tooltip wrapping for icon-only buttons
5. [ ] Test responsive behavior: xs, sm, md, lg, xl breakpoints
6. [ ] Run accessibility audit: axe-core, keyboard nav, focus indicators
7. [ ] Verify color contrast (4.5:1 minimum)
8. [ ] Remove legacy CSS files that are no longer used
9. [ ] Build and verify bundle size <50KB increase
10. [ ] Run full test suite

**Deliverables**:
- All icons migrated to @mui/icons-material
- `docs/accessibility-audit.md` - Checklist results
- Build report with bundle analysis
- Legacy CSS files removed

**Test Strategy**:
- Automated: All existing tests pass
- Automated: Lighthouse accessibility score 100
- Manual: Full user journey: login → navigate → CRUD operations

---

## Dependencies & Risks

| Dependency / Risk | Impact | Mitigation |
|-------------------|--------|------------|
| MUI v6 breaking changes | Migration issues | Check changelog weekly, pin to exact version |
| Bundle size blowout | Performance degradation | Path imports only, lazy load DataGrid, monitor build |
| Component test failures | Coverage gaps | Update tests incrementally with each component |
| Style conflicts (old + new) | Visual inconsistency | Keep old CSS scoped, remove only after verification |
| Accessibility regressions | Compliance failure | Accessibility checklist per phase, axe-core in CI |
| Responsive issues on tablets | Poor UX | Test on physical devices or responsive mode in browser |

---

## Open Questions

1. **Brand colors**: Confirm primary (#1976d2?) and secondary colors with design team
2. **Dark mode default**: System preference or light default?
3. **DataGrid Pro**: Any need for advanced features (column pinning, tree data) in future?
4. **Animation preference**: Keep simple or add page transitions?
5. **SSR consideration**: Not currently used, but verify no issues if added later

---

## Success Criteria Verification

| Criterion | How Verified | Target |
|-----------|--------------|--------|
| Component coverage | Audit: grep for remaining vanilla CSS classes | 100% |
| Visual regression | Manual screenshot comparison | Intent matched |
| Bundle size | Build analyzer | <50KB increase |
| Lighthouse accessibility | Lighthouse CI | 100 |
| Lighthouse performance | Lighthouse CI | ≥90 |
| Build warnings | CI output | Zero MUI deprecation warnings |
| Test pass rate | CI test run | 100% passing |
| Theme consistency | Code review | Zero hardcoded colors |

---

## Task Breakdown Reference

See [tasks.md](tasks.md) for detailed task list with T-IDs.
