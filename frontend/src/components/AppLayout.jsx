import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  AppBar,
  Box,
  Container,
  CssBaseline,
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
  Tooltip,
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import DashboardIcon from '@mui/icons-material/Dashboard';
import PeopleIcon from '@mui/icons-material/People';
import GroupWorkIcon from '@mui/icons-material/GroupWork';
import SettingsIcon from '@mui/icons-material/Settings';
import SupervisorAccountIcon from '@mui/icons-material/SupervisorAccount';
import MonitorIcon from '@mui/icons-material/Monitor';
import { authApi, isAuthenticated, setAuthErrorHandler, clearSessionExpiryHandler } from '../api/auth.js';

// Navigation items configuration
const NAV_ITEMS = [
  { label: 'Agent Roles', path: '/roles', icon: PeopleIcon },
  { label: 'Compositions', path: '/compositions', icon: GroupWorkIcon },
  { label: 'Monitor', path: '/monitor', icon: MonitorIcon },
  { label: 'Users', path: '/users', icon: SupervisorAccountIcon },
  { label: 'Settings', path: '/settings', icon: SettingsIcon },
];

const DRAWER_WIDTH = 240;

/**
 * AppLayout - Main application layout with responsive navigation
 *
 * Features:
 * - Persistent drawer on desktop (md+)
 * - Temporary (overlay) drawer on mobile
 * - Responsive AppBar with hamburger menu on mobile
 * - Consistent branding and user actions
 */
export default function AppLayout({ children }) {
  const location = useLocation();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [authenticated, setAuthenticated] = useState(isAuthenticated());

  // Handle auth state
  React.useEffect(() => {
    setAuthenticated(isAuthenticated());
    setAuthErrorHandler(() => setAuthenticated(false));
    return () => clearSessionExpiryHandler();
  }, []);

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleLogout = async () => {
    await authApi.logout();
    setAuthenticated(false);
    navigate('/login');
  };

  // Drawer content
  const drawerContent = (
    <Box sx={{ width: DRAWER_WIDTH, height: '100%' }}>
      <Toolbar
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'flex-start',
          px: 2,
          borderBottom: 1,
          borderColor: 'divider',
        }}
      >
        <DashboardIcon sx={{ mr: 1, color: 'primary.main' }} />
        <Typography variant="h6" component="div" sx={{ fontWeight: 600 }}>
          Syntexa
        </Typography>
      </Toolbar>
      <Box sx={{ overflow: 'auto' }}>
        <List>
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <ListItem key={item.path} disablePadding>
                <ListItemButton
                  component={Link}
                  to={item.path}
                  selected={isActive}
                  onClick={() => setMobileOpen(false)}
                  sx={{
                    '&.Mui-selected': {
                      backgroundColor: 'action.selected',
                    },
                  }}
                >
                  <ListItemIcon>
                    <Icon color={isActive ? 'primary' : 'inherit'} />
                  </ListItemIcon>
                  <ListItemText
                    primary={item.label}
                    primaryTypographyProps={{
                      fontWeight: isActive ? 600 : 400,
                    }}
                  />
                </ListItemButton>
              </ListItem>
            );
          })}
        </List>
      </Box>

      {authenticated && (
        <Box sx={{ position: 'absolute', bottom: 0, width: '100%', p: 2, borderTop: 1, borderColor: 'divider' }}>
          <ListItem disablePadding>
            <ListItemButton onClick={handleLogout}>
              <ListItemText primary="Logout" />
            </ListItemButton>
          </ListItem>
        </Box>
      )}
    </Box>
  );

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <CssBaseline />

      {/* AppBar */}
      <AppBar
        position="fixed"
        sx={{
          width: { md: `calc(100% - ${DRAWER_WIDTH}px)` },
          ml: { md: `${DRAWER_WIDTH}px` },
          boxShadow: 1,
        }}
      >
        <Toolbar>
          {/* Hamburger menu - visible only on mobile */}
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { md: 'none' } }}
          >
            <MenuIcon />
          </IconButton>

          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            {NAV_ITEMS.find((item) => item.path === location.pathname)?.label || 'Syntexa'}
          </Typography>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {/* User menu placeholder - can be extended */}
            {authenticated && (
              <Tooltip title="Logged in">
                <IconButton color="inherit">
                  <SupervisorAccountIcon />
                </IconButton>
              </Tooltip>
            )}
          </Box>
        </Toolbar>
      </AppBar>

      {/* Drawer - Mobile: temporary overlay, Desktop: permanent */}
      <Box component="nav" sx={{ width: { md: DRAWER_WIDTH }, flexShrink: { md: 0 } }}>
        {/* Mobile drawer */}
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{ keepMounted: true }}
          sx={{
            display: { xs: 'block', md: 'none' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: DRAWER_WIDTH },
          }}
        >
          {drawerContent}
        </Drawer>

        {/* Desktop drawer */}
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', md: 'block' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: DRAWER_WIDTH },
          }}
          open
        >
          {drawerContent}
        </Drawer>
      </Box>

      {/* Main content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          bgcolor: 'background.default',
          p: 3,
          width: { md: `calc(100% - ${DRAWER_WIDTH}px)` },
          mt: '64px', // Account for AppBar height
        }}
      >
        <Container maxWidth="lg" sx={{ py: 2 }}>
          {children}
        </Container>
      </Box>
    </Box>
  );
}
