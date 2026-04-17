# Quickstart Guide: Frontend MUI Refactor

**Phase**: 004 - Frontend MUI Refactor  
**Last Updated**: 2026-04-17

---

## For Developers

### Prerequisites

- Node.js >= 18 (for Bun compatibility)
- Bun package manager (`npm install -g bun`)
- Familiarity with React and MUI v6

### Setup

```bash
# From repo root
cd dashboard

# Install dependencies (first time)
bun install

# Install MUI packages (one-time setup for this phase)
bun add @mui/material @emotion/react @emotion/styled @mui/icons-material
bun add @mui/x-data-grid
```

### Development Workflow

```bash
# Start dev server
bun run dev

# Run tests
bun test

# Type check (if using TypeScript)
bunx tsc --noEmit

# Build for production
bun run build
```

### Code Structure

```
dashboard/src/
├── components/
│   ├── ThemeProvider.jsx    # Theme context + dark mode
│   ├── AppLayout.jsx        # AppBar + Drawer shell
│   ├── NavList.jsx          # Navigation sidebar
│   ├── LoadingFallback.jsx  # Suspense fallback
│   ├── SnackbarProvider.jsx # Global notifications
│   └── ...                  # Page-specific components
├── pages/
│   ├── Login.jsx            # MUI Card + form
│   ├── Users.jsx            # DataGrid table
│   ├── Roles.jsx            # Forms + tables
│   ├── Compositions.jsx     # Drag ordering
│   ├── Settings.jsx         # Switches + sliders
│   └── Monitor.jsx          # Cards + status displays
├── theme.js                 # MUI theme customization
└── main.jsx                 # App entry with ThemeProvider
```

---

## Key Patterns

### Theme Usage

```javascript
import { useTheme } from '@mui/material/styles';
import { Box } from '@mui/material';

function MyComponent() {
  const theme = useTheme();

  return (
    <Box sx={{
      bgcolor: theme.palette.background.paper,
      p: theme.spacing(3),  // 24px (3 * 8px base)
    }}>
      Content
    </Box>
  );
}
```

### Responsive Layout

```javascript
import { Grid, useMediaQuery } from '@mui/material';
import { useTheme } from '@mui/material/styles';

function ResponsiveComponent() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  return (
    <Grid container spacing={2}>
      <Grid item xs={12} md={6}>
        {/* Full width on mobile, half on desktop */}
      </Grid>
      <Grid item xs={12} md={6}>
        Hidden mobile: {isMobile && <span>Mobile view</span>}
      </Grid>
    </Grid>
  );
}
```

### Form Pattern

```javascript
import { TextField, Button, Box } from '@mui/material';

function MyForm() {
  const [values, setValues] = React.useState({ email: '' });
  const [errors, setErrors] = React.useState({});
  const [isSubmitting, setIsSubmitting] = React.useState(false);

  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      await submitData(values);
    } catch (e) {
      setErrors({ email: e.message });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Box component="form" onSubmit={handleSubmit}>
      <TextField
        label="Email"
        value={values.email}
        onChange={(e) => setValues({ ...values, email: e.target.value })}
        error={!!errors.email}
        helperText={errors.email}
        fullWidth
        margin="normal"
      />
      <Button
        type="submit"
        variant="contained"
        disabled={isSubmitting}
        loading={isSubmitting}
      >
        Submit
      </Button>
    </Box>
  );
}
```

### DataGrid Pattern

```javascript
import { DataGrid } from '@mui/x-data-grid';
import { IconButton } from '@mui/material';
import { Edit, Delete } from '@mui/icons-material';

const columns = [
  { field: 'name', headerName: 'Name', flex: 1 },
  { field: 'email', headerName: 'Email', flex: 1 },
  {
    field: 'actions',
    headerName: 'Actions',
    width: 120,
    renderCell: (params) => (
      <>
        <IconButton onClick={() => edit(params.row)} size="small">
          <Edit fontSize="small" />
        </IconButton>
        <IconButton onClick={() => remove(params.row.id)} size="small">
          <Delete fontSize="small" />
        </IconButton>
      </>
    )
  }
];

<DataGrid
  rows={data}
  columns={columns}
  pageSizeOptions={[10, 25, 50]}
  initialState={{
    pagination: { paginationModel: { pageSize: 25 } }
  }}
  checkboxSelection
  disableRowSelectionOnClick
/>
```

---

## Migration Checklist

When migrating a component:

- [ ] Replace CSS classes with `sx` prop or `styled()`
- [ ] Update imports to path imports (`@mui/material/Button`)
- [ ] Add Typography for text with semantic hierarchy
- [ ] Use Box/Container for layout instead of divs
- [ ] Replace buttons with MUI Button component
- [ ] Replace inputs with MUI TextField
- [ ] Add loading states with CircularProgress or Skeleton
- [ ] Add error display with Alert or Snackbar
- [ ] Test keyboard navigation (Tab order, focus)
- [ ] Verify responsive behavior on mobile/desktop

---

## Testing

### Component Tests

```javascript
import { render, screen, fireEvent } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import theme from '../theme';

const renderWithTheme = (component) =>
  render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );

test('button renders with correct text', () => {
  renderWithTheme(<Button>Click me</Button>);
  expect(screen.getByText('Click me')).toBeInTheDocument();
});
```

### Visual Regression

Use Storybook or Chromatic for visual testing:

```bash
# Install storybook
bunx sb init

# Run storybook
bunx sb dev
```

---

## Troubleshooting

### "Module not found" errors

Ensure path imports:
```javascript
// ✅ Correct
import Button from '@mui/material/Button';

// ❌ May cause tree-shaking issues
import { Button } from '@mui/material';
```

### Theme not applied

Check ThemeProvider wraps your app:
```javascript
// main.jsx
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import theme from './theme';

<ThemeProvider theme={theme}>
  <CssBaseline />
  <App />
</ThemeProvider>
```

### Bundle too large

Check for barrel imports:
```bash
# Analyze bundle
bunx vite-bundle-visualizer
```

### Styles not overriding

Use `sx` for one-off overrides, `styled()` for reusable:
```javascript
// sx prop
<Box sx={{ backgroundColor: 'custom.color' }} />

// styled component
const CustomBox = styled(Box)(({ theme }) => ({
  backgroundColor: theme.palette.custom.main,
}));
```

---

## Resources

- [MUI v6 Docs](https://mui.com/material-ui/getting-started/)
- [DataGrid Docs](https://mui.com/x/react-data-grid/)
- [MUI Icons](https://mui.com/material-ui/material-icons/)
- [Theme Customization](https://mui.com/material-ui/customization/theming/)
- [Responsive Grid](https://mui.com/material-ui/react-grid/)
