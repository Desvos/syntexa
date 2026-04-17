# Data Model: Frontend MUI Refactor

**Status**: Draft  
**Created**: 2026-04-17  
**Phase**: 004 - Frontend MUI Refactor

---

## Overview

This phase is a **frontend-only refactor** - no backend data models change. Data models here represent:
1. **Theme Configuration** (stored in localStorage and code)
2. **Component State** (React state management)
3. **UI Constants** (enum mappings)

---

## Theme Configuration

### ThemeSettings (localStorage + React Context)

| Field | Type | Storage | Description |
|-------|------|---------|-------------|
| `mode` | `'light' \| 'dark'` | localStorage | Active theme mode |
| `systemPreference` | `boolean` | localStorage | Whether to follow OS preference |
| `customPrimary` | `string?` | localStorage | Custom primary color hex |
| `customSecondary` | `string?` | localStorage | Custom secondary color hex |

### Theme Structure (Code-defined)

```typescript
// Theme tokens defined in theme.ts
interface SyntexaTheme {
  palette: {
    primary: { main: string; dark: string; light: string };
    secondary: { main: string; dark: string; light: string };
    background: { default: string; paper: string; };
    text: { primary: string; secondary: string; };
    error: { main: string; };
    warning: { main: string; };
    success: { main: string; };
    info: { main: string; };
  };
  typography: {
    fontFamily: string;
    h1: TypographyStyle;
    h2: TypographyStyle;
    h3: TypographyStyle;
    body1: TypographyStyle;
    body2: TypographyStyle;
    button: TypographyStyle;
  };
  spacing: (factor: number) => number; // 8px base
  breakpoints: Breakpoints;
}
```

---

## Component State Models

### NavigationState (React State)

| Field | Type | Description |
|-------|------|-------------|
| `drawerOpen` | `boolean` | Mobile drawer visibility |
| `activeSection` | `string` | Currently active nav section |

### TableState (React State - per DataGrid)

| Field | Type | Description |
|-------|------|-------------|
| `paginationModel` | `{ page: number; pageSize: number }` | Current page and size |
| `sortModel` | `GridSortModel` | Active sort columns |
| `filterModel` | `GridFilterModel` | Active filters |
| `selectionModel` | `GridRowSelectionModel` | Selected row IDs |

### FormState (React State - per form)

| Field | Type | Description |
|-------|------|-------------|
| `values` | `Record<string, any>` | Form field values |
| `errors` | `Record<string, string>` | Field validation errors |
| `touched` | `Record<string, boolean>` | Fields user has interacted with |
| `isSubmitting` | `boolean` | Form submission in progress |
| `isValid` | `boolean` | Overall form validity |

### DialogState (React State)

| Field | Type | Description |
|-------|------|-------------|
| `open` | `boolean` | Dialog visibility |
| `type` | `'confirm' \| 'form' \| 'alert'` | Dialog variant |
| `title` | `string` | Dialog title text |
| `content` | `ReactNode` | Dialog body content |
| `confirmAction` | `() => void` | Confirm callback |

### SnackbarState (React State)

| Field | Type | Description |
|-------|------|-------------|
| `open` | `boolean` | Snackbar visibility |
| `message` | `string` | Display message |
| `severity` | `'success' \| 'error' \| 'warning' \| 'info'` | Alert variant |
| `autoHideDuration` | `number` | Milliseconds before auto-hide |

---

## UI Constants

### NavigationItems

```typescript
const NAV_ITEMS = [
  { label: 'Dashboard', path: '/', icon: 'Dashboard' },
  { label: 'Agent Roles', path: '/roles', icon: 'People' },
  { label: 'Compositions', path: '/compositions', icon: 'GroupWork' },
  { label: 'Settings', path: '/settings', icon: 'Settings' },
  { label: 'Users', path: '/users', icon: 'SupervisorAccount' },
  { label: 'Monitor', path: '/monitor', icon: 'Monitor' },
] as const;
```

### StatusChipMapping

Maps backend status strings to MUI Chip colors:

| Backend Status | Chip Color | Icon |
|---------------|------------|------|
| `active` | `success` | CheckCircle |
| `completed` | `info` | Done |
| `failed` | `error` | Error |
| `pending` | `warning` | Schedule |
| `running` | `primary` | Sync (spinning) |

### ButtonVariants

| Action Type | MUI Variant | Color |
|-------------|-------------|-------|
| Primary action | `contained` | `primary` |
| Secondary action | `outlined` | `primary` |
| Danger/Delete | `contained` | `error` |
| Text action | `text` | `primary` |
| Icon action | `IconButton` | `default` |

---

## Component Migration Mapping

| Old Component | New MUI Component | Props Changes |
|---------------|-----------------|---------------|
| `<div className="login-form">` | `<Box component="form">` | `sx` prop for styles |
| `<input type="text">` | `<TextField>` | Add `label`, `helperText`, `error` |
| `<button>` | `<Button>` | Use `variant`, `startIcon` |
| `<table>` | `<DataGrid>` | Move to column definitions |
| `<div className="card">` | `<Card>` | Wrap content in `<CardContent>` |
| `<span className="badge">` | `<Chip>` | Use `color`, `size` props |
| `<div className="modal">` | `<Dialog>` | Add `<DialogTitle>`, `<DialogContent>` |
| `<img className="avatar">` | `<Avatar>` | Use `src`, `alt` props |
| `<div className="loading">` | `<CircularProgress>` | Or `<Skeleton>` for content |
| `<span className="icon-*">` | `<SvgIcon>` | Use `@mui/icons-material` |

---

## No Database Changes

This refactor requires **zero backend changes**:
- ✅ No API endpoint modifications
- ✅ No database schema changes
- ✅ Existing responses remain compatible
- ✅ All changes isolated to frontend

---

## TypeScript Interfaces (for reference)

```typescript
// Types added during migration

interface ThemeContextValue {
  mode: 'light' | 'dark';
  toggleMode: () => void;
  setMode: (mode: 'light' | 'dark') => void;
  theme: Theme;
}

interface TablePaginationState {
  page: number;
  pageSize: number;
}

interface FormFieldProps<T = string> {
  name: string;
  label: string;
  value: T;
  onChange: (value: T) => void;
  error?: string;
  required?: boolean;
  disabled?: boolean;
}

interface DataGridColumn<T = any> {
  field: keyof T;
  headerName: string;
  flex?: number;
  width?: number;
  sortable?: boolean;
  filterable?: boolean;
  renderCell?: (params: GridRenderCellParams<T>) => React.ReactNode;
}
```
