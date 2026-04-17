# UI Contracts: Frontend MUI Refactor

**Status**: Draft  
**Created**: 2026-04-17  
**Phase**: 004 - Frontend MUI Refactor

---

## External Interface

The frontend refactor affects the **visual interface** presented to users. These contracts define the expected UI behavior.

---

## Theme Contract

### Theme Mode

| Property | Values | Default | Storage |
|----------|--------|-----------|---------|
| `mode` | `'light' \| 'dark'` | `'light'` | localStorage |
| `systemPreference` | `boolean` | `true` | localStorage |

### Theme Tokens (CSS Custom Properties)

```css
/* Injected via ThemeProvider */
--mui-palette-primary-main: #1976d2;
--mui-palette-secondary-main: #dc004e;
--mui-palette-background-default: #f5f5f5;
--mui-palette-background-paper: #ffffff;
--mui-spacing-unit: 8px;
```

---

## Component Interface Contracts

### Form Components

#### TextField

```typescript
interface TextFieldProps {
  name: string;           // Form field identifier
  label: string;          // Visible label text
  value: string;          // Controlled value
  onChange: (value: string) => void;
  error?: string;         // Error message to display
  helperText?: string;    // Hint text below field
  required?: boolean;
  disabled?: boolean;
  type?: 'text' | 'password' | 'email' | 'number';
  multiline?: boolean;    // Use textarea
  rows?: number;          // For multiline
}
```

#### Select

```typescript
interface SelectProps<T = string> {
  name: string;
  label: string;
  value: T;
  options: Array<{ value: T; label: string }>;
  onChange: (value: T) => void;
  error?: string;
  required?: boolean;
  disabled?: boolean;
}
```

#### Button

```typescript
interface ButtonProps {
  children: ReactNode;        // Button text
  variant: 'contained' | 'outlined' | 'text';
  color: 'primary' | 'secondary' | 'error';
  onClick: () => void;
  disabled?: boolean;
  loading?: boolean;          // Shows CircularProgress
  startIcon?: ReactNode;      // MUI Icon component
  type?: 'button' | 'submit' | 'reset';
}
```

### Data Display Components

#### DataGrid

```typescript
interface DataGridProps<T = any> {
  rows: T[];
  columns: GridColumn<T>[];   // Column definitions
  loading?: boolean;          // Shows loading overlay
  pagination?: boolean;
  pageSizeOptions?: number[]; // Default: [10, 25, 50]
  checkboxSelection?: boolean;
  onRowClick?: (row: T) => void;
  onSelectionChange?: (selectedIds: string[]) => void;
}

interface GridColumn<T> {
  field: keyof T;
  headerName: string;
  flex?: number;
  width?: number;
  sortable?: boolean;
  filterable?: boolean;
  hideable?: boolean;
}
```

#### Card

```typescript
interface CardProps {
  children: ReactNode;
  title?: string;           // Card header title
  actions?: ReactNode;        // Footer action buttons
  elevation?: number;         // Shadow depth (0-24)
}
```

#### Chip

```typescript
interface ChipProps {
  label: string;
  color: 'default' | 'primary' | 'secondary' | 'success' | 'error' | 'warning' | 'info';
  variant?: 'filled' | 'outlined';
  size?: 'small' | 'medium';
  icon?: ReactNode;
  onDelete?: () => void;      // Shows delete icon
}
```

### Feedback Components

#### Alert

```typescript
interface AlertProps {
  severity: 'success' | 'error' | 'warning' | 'info';
  children: ReactNode;        // Message content
  onClose?: () => void;       // Shows close button
}
```

#### Snackbar

```typescript
interface SnackbarProps {
  open: boolean;
  message: string;
  severity?: 'success' | 'error' | 'warning' | 'info';
  autoHideDuration?: number;  // ms, default 6000
  onClose: () => void;
}
```

#### Progress Indicators

```typescript
// CircularProgress
interface CircularProgressProps {
  size?: number;      // Diameter in px, default 40
  color?: 'primary' | 'secondary' | 'inherit';
}

// Skeleton
interface SkeletonProps {
  variant?: 'text' | 'circular' | 'rectangular' | 'rounded';
  width?: number | string;
  height?: number | string;
  animation?: 'pulse' | 'wave' | false;
}
```

### Layout Components

#### AppLayout

```typescript
interface AppLayoutProps {
  children: ReactNode;
  title?: string;             // Page title for AppBar
  requireAuth?: boolean;      // Wrap with ProtectedRoute
}
```

#### Navigation

```typescript
interface NavItem {
  label: string;
  path: string;
  icon: string;               // MUI icon name (e.g., 'Dashboard')
  exact?: boolean;
}

interface NavListProps {
  items: NavItem[];
  onItemClick?: () => void;   // Called on mobile after selection
}
```

---

## Screen Contracts

### Login Screen

**Layout**: Centered Card with form
**Components**:
- Card (elevation=4)
- CardHeader (title="Login")
- CardContent with:
  - TextField (email) - required, type="email"
  - TextField (password) - required, type="password", visibility toggle
  - Button (variant="contained", fullWidth) - "Sign In"
- Alert (if error) - severity="error"

**States**:
| State | Visual |
|-------|--------|
| Idle | Form editable, button shows "Sign In" |
| Submitting | Button shows CircularProgress, form disabled |
| Error | Alert displayed with error message |

### Users Screen

**Layout**: Card with Toolbar + DataGrid
**Components**:
- Card
- Toolbar with Typography (title) + Button ("Add User")
- DataGrid with columns: name, email, role, status, actions
- actions column: IconButton (edit), IconButton (delete)
- Dialog for create/edit user form
- Chip for status display

### Settings Screen

**Layout**: Card with form sections
**Components**:
- Card with multiple sections
- Switch for boolean settings
- Slider for numeric values (with value display)
- TextField for text/config values
- Alert for connection status
- Button ("Save Changes")

---

## Responsive Behavior

### Breakpoints

| Breakpoint | Width | Layout Changes |
|------------|-------|----------------|
| xs | 0-599px | Mobile: single column, drawer as overlay |
| sm | 600-899px | Tablet: adjusted padding, compact nav |
| md | 900-1199px | Desktop: persistent drawer |
| lg | 1200px+ | Full desktop: generous spacing |

### Grid System

```typescript
// Default container behavior
<Container maxWidth="lg"> // 1200px max
  <Grid container spacing={2}>
    <Grid item xs={12} md={6}> // Full on mobile, half on desktop
      {/* Content */}
    </Grid>
  </Grid>
</Container>
```

---

## Accessibility Requirements

### WCAG 2.1 AA Compliance

| Requirement | Implementation |
|-------------|----------------|
| Keyboard navigation | All interactive elements focusable with Tab |
| Focus indicators | Visible 2px outline on focused elements |
| Color contrast | 4.5:1 minimum for text |
| Screen reader | ARIA labels on icon buttons |
| Form labels | All inputs have associated labels |
| Error announcements | Errors read by screen readers |

### Testing Checklist

- [ ] All buttons accessible via keyboard
- [ ] Dialog traps focus while open
- [ ] Skip link for navigation
- [ ] No color-only information
- [ ] Text zooms to 200% without loss

---

## Icon Mapping

| Semantic Purpose | MUI Icon Name |
|------------------|---------------|
| Dashboard | `Dashboard` |
| Users | `People` or `SupervisorAccount` |
| Roles | `Person` |
| Compositions | `GroupWork` |
| Settings | `Settings` |
| Monitor | `Monitor` |
| Edit action | `Edit` |
| Delete action | `Delete` |
| Add action | `Add` |
| Save | `Save` |
| Cancel | `Close` or `Cancel` |
| Search | `Search` |
| Menu | `Menu` |
| Account | `AccountCircle` |
| Logout | `Logout` |
| Visibility (show) | `Visibility` |
| VisibilityOff (hide) | `VisibilityOff` |
| Success status | `CheckCircle` |
| Error status | `Error` |
| Warning status | `Warning` |
| Info status | `Info` |
| Sync/Loading | `Sync` (spinning) |
| Refresh | `Refresh` |

---

## State Management Contracts

### Theme Context

```typescript
interface ThemeContextType {
  mode: 'light' | 'dark';
  toggleMode: () => void;
  setMode: (mode: 'light' | 'dark') => void;
  theme: Theme;  // MUI theme object
}

// Usage
const { mode, toggleMode } = useTheme();
```

### Snackbar Context

```typescript
interface SnackbarContextType {
  showMessage: (message: string, severity?: AlertSeverity) => void;
  showSuccess: (message: string) => void;
  showError: (message: string) => void;
}

// Usage
const { showSuccess, showError } = useSnackbar();
showSuccess('User created successfully');
```

---

## Animation Specifications

### Theme Transition

```css
/* Smooth theme transition */
* {
  transition: background-color 300ms ease, color 300ms ease;
}

/* Exclude performance-sensitive elements */
.SVGIcon, .CircularProgress {
  transition: none;
}
```

### Dialog Animation

- Open: 225ms ease-out
- Close: 195ms ease-in

### Snackbar Animation

- Slide in from bottom: 300ms
- Auto-hide delay: 6000ms (configurable)
- Slide out: 250ms
