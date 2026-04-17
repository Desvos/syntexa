# Task Breakdown: Frontend MUI Refactor

**Plan**: [plan.md](plan.md)  
**Spec**: [spec.md](spec.md)  
**Data Model**: [data-model.md](data-model.md)  
**Status**: Draft  
**Created**: 2026-04-17  
**Author**: antoniodevivo  

---

## Overview

This breakdown follows the **9-phase plan** from plan.md, organized by component migration priority.

---

## Phase 1: Foundation (Theme & Dependencies)

**Goal**: Install MUI and set up theme infrastructure

### Tasks

- [ ] T001 Install MUI dependencies: `@mui/material`, `@emotion/react`, `@emotion/styled`, `@mui/icons-material`, `@mui/x-data-grid`
- [ ] T002 Create `dashboard/src/theme.js` with custom theme configuration
- [ ] T003 Create `dashboard/src/components/ThemeProvider.jsx` wrapper with dark mode support
- [ ] T004 Wrap App with ThemeProvider in `main.jsx`
- [ ] T005 Create component inventory document: `docs/components-migration.md`
- [ ] T006 Run build and verify no bundle size regression (<50KB)
- [ ] T007 Create `LoadingFallback.jsx` with MUI Skeleton for suspense

---

## Phase 2: Layout Migration

**Goal**: Migrate application shell components

### Tasks

- [ ] T008 Create `dashboard/src/components/AppLayout.jsx` with MUI AppBar, Drawer, Container
- [ ] T009 Migrate navigation to use MUI Drawer (persistent on desktop, temporary on mobile)
- [ ] T010 Create `dashboard/src/components/NavList.jsx` with List, ListItem, ListItemIcon, ListItemText
- [ ] T011 Update page layouts to use MUI Box/Container/Grid
- [ ] T012 Add responsive behavior: drawer collapses on mobile, hamburger menu
- [ ] T013 Create `dashboard/src/components/UserMenu.jsx` for header user actions
- [ ] T014 Update routing integration with new layout wrapper
- [ ] T015 Verify responsive behavior on xs, sm, md, lg breakpoints

---

## Phase 3: Login Page Migration

**Goal**: Complete migration of Login page and form components

### Tasks

- [ ] T016 Create MUI `LoginForm.jsx` with TextField (email, password), Button
- [ ] T017 Add FormControl and validation states (error, helperText)
- [ ] T018 Add visibility toggle for password field (IconButton with Visibility icon)
- [ ] T019 Add loading state with CircularProgress in Button
- [ ] T020 Update `Login.jsx` page with MUI Card, CardContent for form container
- [ ] T021 Add Alert component for login error display
- [ ] T022 Verify form accessibility (labels, focus management)
- [ ] T023 Update/rewrite component tests for new implementation

---

## Phase 4: User Management Migration

**Goal**: Migrate Users page and table to DataGrid

### Tasks

- [ ] T024 Create new `UsersTable.jsx` using DataGrid component
- [ ] T025 Define columns: name, email, role, status, actions
- [ ] T026 Add actions column with IconButton (edit, delete)
- [ ] T027 Implement row selection with checkboxSelection
- [ ] T028 Add pagination with pageSize options [10, 25, 50]
- [ ] T029 Create `UserDialog.jsx` for create/edit user modals using MUI Dialog
- [ ] T030 Replace form inputs with MUI TextField, Select components
- [ ] T031 Update `Users.jsx` page with MUI layout containers
- [ ] T032 Add Toolbar with Button for "Add User" action

---

## Phase 5: Agent Roles Migration

**Goal**: Migrate Roles page, table, and editor to MUI

### Tasks

- [ ] T033 Create `RolesTable.jsx` with DataGrid (columns: name, model, status, actions)
- [ ] T034 Use Chip component for status display
- [ ] T035 Create `RoleEditor.jsx` with MUI form components
- [ ] T036 Add TextField for name with validation
- [ ] T037 Add Select for model/provider dropdowns
- [ ] T038 Add TextField (multiline) for system prompt with character counter
- [ ] T039 Create `HandoffTargets.jsx` with MUI Switch for toggle selection
- [ ] T040 Update `Roles.jsx` page with MUI Card layouts
- [ ] T041 Add Dialog for confirmation on delete

---

## Phase 6: Compositions Migration

**Goal**: Migrate Swarm Compositions page

### Tasks

- [ ] T042 Create `CompositionsTable.jsx` with DataGrid
- [ ] T043 Create `CompositionEditor.jsx` with form fields
- [ ] T044 Create `RoleOrder.jsx` drag-to-reorder using MUI List + icons
- [ ] T045 Use Chip for displaying ordered roles in table
- [ ] T046 Create `TaskTypeSelect.jsx` with MUI Select
- [ ] T047 Update `Compositions.jsx` page
- [ ] T048 Add Card-based layout for viewing compositions

---

## Phase 7: Settings & Monitor Migration

**Goal**: Migrate Settings and Monitor pages with feedback components

### Tasks

- [ ] T049 Update `Settings.jsx` with MUI form controls
- [ ] T050 Add Switch for boolean settings
- [ ] T051 Add Slider for numeric settings (polling interval)
- [ ] T052 Add TextField for token/config inputs
- [ ] T053 Create `ConnectionStatus.jsx` with MUI Alert (success/error variants)
- [ ] T054 Update `Monitor.jsx` with MUI Card layout
- [ ] T055 Create `ActiveSwarms.jsx` with DataGrid for active tasks
- [ ] T056 Create `CompletedSwarms.jsx` with DataGrid for history
- [ ] T057 Create `LogViewer.jsx` with MUI Paper + scrolling container
- [ ] T058 Add Skeleton loading states for data fetching

---

## Phase 8: Feedback & Theme Components

**Goal**: Add comprehensive feedback components and theme toggle

### Tasks

- [ ] T059 Create `SnackbarProvider.jsx` for app-wide notifications
- [ ] T060 Add Snackbar hooks for success/error messages
- [ ] T061 Update UserMenu with theme toggle (light/dark/system)
- [ ] T062 Add theme persistence to localStorage
- [ ] T063 Create theme transition (CssVarsProvider or CSS transition)
- [ ] T064 Add Backdrop component for full-screen loading states
- [ ] T065 Create `ErrorBoundary.jsx` with MUI Alert fallback
- [ ] T066 Add CircularProgress for async button states throughout

---

## Phase 9: Icon Migration & Final Polish

**Goal**: Replace all remaining icons and finalize styling

### Tasks

- [ ] T067 Audit all icon usage: grep for `<svg`, emoji, `className="icon`
- [ ] T068 Replace with @mui/icons-material equivalents
- [ ] T069 IconButton for all clickable icons
- [ ] T070 Tooltip wrapping for icon-only buttons
- [ ] T071 Test responsive behavior: xs, sm, md, lg, xl breakpoints
- [ ] T072 Run accessibility audit: axe-core, keyboard nav, focus indicators
- [ ] T073 Verify color contrast (4.5:1 minimum)
- [ ] T074 Remove legacy CSS files that are no longer used
- [ ] T075 Build and verify bundle size <50KB increase
- [ ] T076 Run full test suite

---

## Dependency Graph

```
Phase 1 (Foundation)
    ↓
Phase 2 (Layout) → All other phases depend on this
    ↓
Phase 3 (Login) → Can run in parallel with Phase 4 after Phase 2
    ↓
Phase 4 (Users) → Phase 5, 6 can run in parallel
    ↓
Phase 5 (Roles) → Independent after Phase 4
    ↓
Phase 6 (Compositions) → Independent after Phase 4
    ↓
Phase 7 (Settings/Monitor) → Depends on Phase 2-6
    ↓
Phase 8 (Feedback) → Can run in parallel with Phase 7
    ↓
Phase 9 (Polish) → Requires all previous phases complete
```

## Parallel Execution

After Phase 2, these are independent:
- Phase 3 (Login) - Simple, good starter
- Phase 4 (Users) - Table pattern for others
- Phase 5 (Roles) - Forms + Tables
- Phase 6 (Compositions) - Forms + Tables

Phase 7 (Settings/Monitor) needs components from all above.
Phase 8 and 9 are final polish phases.

---

## Task Count Summary

| Phase | Task Count | Focus |
|-------|-----------|-------|
| Phase 1: Foundation | 7 | Theme, dependencies, inventory |
| Phase 2: Layout | 8 | App shell, navigation, responsive |
| Phase 3: Login | 8 | Forms, validation, accessibility |
| Phase 4: Users | 9 | DataGrid, CRUD dialogs |
| Phase 5: Roles | 9 | Complex forms, handoff targets |
| Phase 6: Compositions | 7 | Role ordering, selects |
| Phase 7: Settings/Monitor | 10 | Switches, sliders, DataGrids |
| Phase 8: Feedback | 8 | Notifications, theme toggle |
| Phase 9: Polish | 10 | Icons, accessibility, cleanup |
| **Total** | **76** | **9 Phases** |

---

## Constitution Compliance Summary

| Principle | Tasks Tagged | Coverage |
|-----------|-------------|----------|
| Clarity First | All T001-T076 | Full - MUI patterns are well-documented |
| Test-Driven | T023, T071-T076 | Partial - Component tests + final verification |
| Modular Architecture | T001-T009 | Full - Components remain isolated |
| Security by Default | T052 (token inputs) | Partial - No security changes needed |

---

## Critical Path

For MVP (usable dashboard after migration):
```
T001-T007 (Foundation) → T008-T015 (Layout) →
T016-T023 (Login) → T024-T032 (Users) →
T049-T052 (Settings forms) →
T071-T076 (Final polish)
```

This delivers a working, themed dashboard with login, users, and settings.

---

## Estimated Timeline

**Solo developer, incremental per day:**
- Week 1: Phases 1-2 (Foundation + Layout)
- Week 2: Phases 3-4 (Login + Users)
- Week 3: Phases 5-6 (Roles + Compositions)
- Week 4: Phases 7-8 (Settings/Monitor + Feedback)
- Week 5: Phase 9 (Polish, icons, cleanup, testing)

**Total: 5 weeks** (conservative, allows review between phases)
