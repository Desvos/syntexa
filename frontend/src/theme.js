import { createTheme, alpha } from '@mui/material/styles';

const brand = {
  primary: {
    main: '#6366f1',
    dark: '#4f46e5',
    light: '#818cf8',
    contrastText: '#ffffff',
  },
  secondary: {
    main: '#14b8a6',
    dark: '#0f766e',
    light: '#2dd4bf',
    contrastText: '#ffffff',
  },
};

const sharedTypography = {
  fontFamily:
    '"Inter", "Roboto", "Helvetica", "Arial", -apple-system, BlinkMacSystemFont, sans-serif',
  h1: { fontSize: '2.5rem', fontWeight: 700, letterSpacing: '-0.02em' },
  h2: { fontSize: '2rem', fontWeight: 700, letterSpacing: '-0.02em' },
  h3: { fontSize: '1.75rem', fontWeight: 600, letterSpacing: '-0.01em' },
  h4: { fontSize: '1.5rem', fontWeight: 600, letterSpacing: '-0.01em' },
  h5: { fontSize: '1.25rem', fontWeight: 600 },
  h6: { fontSize: '1rem', fontWeight: 600 },
  subtitle1: { fontWeight: 500 },
  subtitle2: { fontWeight: 600, letterSpacing: '0.01em' },
  button: { textTransform: 'none', fontWeight: 600, letterSpacing: '0.01em' },
};

const buildComponents = (mode) => ({
  MuiCssBaseline: {
    styleOverrides: {
      body: {
        scrollbarColor:
          mode === 'dark' ? '#4b5563 #1f2937' : '#cbd5e1 #f1f5f9',
        '&::-webkit-scrollbar, & *::-webkit-scrollbar': {
          width: 10,
          height: 10,
        },
        '&::-webkit-scrollbar-thumb, & *::-webkit-scrollbar-thumb': {
          borderRadius: 8,
          backgroundColor: mode === 'dark' ? '#4b5563' : '#cbd5e1',
          minHeight: 24,
        },
        '&::-webkit-scrollbar-thumb:hover, & *::-webkit-scrollbar-thumb:hover': {
          backgroundColor: mode === 'dark' ? '#6b7280' : '#94a3b8',
        },
      },
    },
  },
  MuiButton: {
    defaultProps: { disableElevation: true },
    styleOverrides: {
      root: {
        borderRadius: 10,
        paddingInline: 16,
        paddingBlock: 8,
      },
      containedPrimary: {
        background: `linear-gradient(135deg, ${brand.primary.main} 0%, ${brand.primary.dark} 100%)`,
        '&:hover': {
          background: `linear-gradient(135deg, ${brand.primary.dark} 0%, ${brand.primary.main} 100%)`,
        },
      },
      sizeLarge: {
        paddingBlock: 12,
        fontSize: '1rem',
      },
    },
  },
  MuiIconButton: {
    styleOverrides: {
      root: {
        borderRadius: 10,
      },
    },
  },
  MuiCard: {
    defaultProps: { elevation: 0 },
    styleOverrides: {
      root: {
        borderRadius: 14,
        border: `1px solid ${mode === 'dark' ? '#27272a' : '#e5e7eb'}`,
        backgroundImage: 'none',
        transition: 'border-color 180ms ease, box-shadow 180ms ease',
      },
    },
  },
  MuiCardHeader: {
    styleOverrides: {
      root: {
        padding: '16px 20px',
      },
      title: {
        fontSize: '1rem',
        fontWeight: 600,
      },
    },
  },
  MuiCardContent: {
    styleOverrides: {
      root: {
        padding: 20,
        '&:last-child': { paddingBottom: 20 },
      },
    },
  },
  MuiPaper: {
    styleOverrides: {
      root: {
        backgroundImage: 'none',
      },
    },
  },
  MuiAppBar: {
    defaultProps: { color: 'transparent', elevation: 0 },
    styleOverrides: {
      root: {
        backdropFilter: 'saturate(180%) blur(12px)',
        backgroundColor:
          mode === 'dark'
            ? alpha('#0f172a', 0.8)
            : alpha('#ffffff', 0.8),
        borderBottom: `1px solid ${
          mode === 'dark' ? '#27272a' : '#e5e7eb'
        }`,
        color: mode === 'dark' ? '#f8fafc' : '#0f172a',
      },
    },
  },
  MuiDrawer: {
    styleOverrides: {
      paper: {
        borderRight: `1px solid ${mode === 'dark' ? '#27272a' : '#e5e7eb'}`,
        backgroundImage: 'none',
        backgroundColor: mode === 'dark' ? '#0b1220' : '#ffffff',
      },
    },
  },
  MuiListItemButton: {
    styleOverrides: {
      root: {
        borderRadius: 10,
        marginInline: 8,
        marginBlock: 2,
        '&.Mui-selected': {
          backgroundColor: alpha(brand.primary.main, mode === 'dark' ? 0.18 : 0.1),
          color: brand.primary.main,
          '& .MuiListItemIcon-root': { color: brand.primary.main },
          '&:hover': {
            backgroundColor: alpha(brand.primary.main, mode === 'dark' ? 0.26 : 0.16),
          },
        },
      },
    },
  },
  MuiListItemIcon: {
    styleOverrides: {
      root: {
        minWidth: 36,
        color: mode === 'dark' ? '#94a3b8' : '#64748b',
      },
    },
  },
  MuiChip: {
    styleOverrides: {
      root: {
        borderRadius: 8,
        fontWeight: 500,
      },
    },
  },
  MuiTextField: {
    defaultProps: { variant: 'outlined', size: 'small' },
  },
  MuiOutlinedInput: {
    styleOverrides: {
      root: {
        borderRadius: 10,
      },
    },
  },
  MuiAlert: {
    styleOverrides: {
      root: { borderRadius: 12 },
    },
  },
  MuiTooltip: {
    styleOverrides: {
      tooltip: {
        borderRadius: 8,
        fontSize: '0.75rem',
        paddingInline: 10,
        paddingBlock: 6,
      },
    },
  },
  MuiDialog: {
    styleOverrides: {
      paper: {
        borderRadius: 16,
      },
    },
  },
  MuiDivider: {
    styleOverrides: {
      root: {
        borderColor: mode === 'dark' ? '#27272a' : '#e5e7eb',
      },
    },
  },
  MuiTableCell: {
    styleOverrides: {
      root: {
        borderColor: mode === 'dark' ? '#27272a' : '#e5e7eb',
      },
      head: {
        fontWeight: 600,
        fontSize: '0.75rem',
        textTransform: 'uppercase',
        letterSpacing: '0.06em',
        color: mode === 'dark' ? '#94a3b8' : '#64748b',
      },
    },
  },
});

export const lightTheme = createTheme({
  palette: {
    mode: 'light',
    primary: brand.primary,
    secondary: brand.secondary,
    background: {
      default: '#f8fafc',
      paper: '#ffffff',
    },
    text: {
      primary: '#0f172a',
      secondary: '#475569',
    },
    divider: '#e5e7eb',
    error: { main: '#ef4444' },
    warning: { main: '#f59e0b' },
    success: { main: '#10b981' },
    info: { main: '#3b82f6' },
  },
  typography: sharedTypography,
  shape: { borderRadius: 10 },
  spacing: 8,
  components: buildComponents('light'),
});

export const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: brand.primary,
    secondary: brand.secondary,
    background: {
      default: '#0b1220',
      paper: '#111827',
    },
    text: {
      primary: '#f8fafc',
      secondary: '#94a3b8',
    },
    divider: '#27272a',
    error: { main: '#f87171' },
    warning: { main: '#fbbf24' },
    success: { main: '#34d399' },
    info: { main: '#60a5fa' },
  },
  typography: sharedTypography,
  shape: { borderRadius: 10 },
  spacing: 8,
  components: buildComponents('dark'),
});

export default lightTheme;
