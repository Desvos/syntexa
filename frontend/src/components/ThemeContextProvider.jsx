import React, { createContext, useContext, useEffect, useState } from 'react';
import { ThemeProvider as MuiThemeProvider, CssBaseline } from '@mui/material';
import { lightTheme, darkTheme } from '../theme.js';

// Create context for theme
const ThemeContext = createContext({
  mode: 'light',
  toggleMode: () => {},
  setMode: () => {},
  prefersSystem: true,
});

// Hook to use theme context
export const useThemeMode = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useThemeMode must be used within ThemeContextProvider');
  }
  return context;
};

/**
 * ThemeContextProvider - Provides MUI theme with dark mode support
 *
 * Features:
 * - Light/Dark mode toggle
    * - localStorage persistence
    * - Optional system preference detection
    */
export function ThemeContextProvider({ children }) {
  // Initialize from localStorage or default to system preference
  const [mode, setMode] = useState(() => {
    if (typeof window === 'undefined') return 'light';
    const saved = localStorage.getItem('syntexa-theme-mode');
    if (saved === 'light' || saved === 'dark') return saved;
    // Default to light
    return 'light';
  });

  // Get current theme object based on mode
  const theme = mode === 'dark' ? darkTheme : lightTheme;

  // Persist theme to localStorage
  useEffect(() => {
    localStorage.setItem('syntexa-theme-mode', mode);
    // Add data-theme attribute for CSS (optional for legacy components)
    document.documentElement.setAttribute('data-theme', mode);
  }, [mode]);

  // Toggle between light and dark
  const toggleMode = () => {
    setMode((prevMode) => (prevMode === 'light' ? 'dark' : 'light'));
  };

  // Set specific mode
  const setThemeMode = (newMode) => {
    if (newMode === 'light' || newMode === 'dark') {
      setMode(newMode);
    }
  };

  const contextValue = {
    mode,
    toggleMode,
    setMode: setThemeMode,
    isDark: mode === 'dark',
  };

  return (
    <ThemeContext.Provider value={contextValue}>
      <MuiThemeProvider theme={theme}>
        <CssBaseline />
        {children}
      </MuiThemeProvider>
    </ThemeContext.Provider>
  );
}

export default ThemeContextProvider;
