import React, { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  AppBar,
  Box,
  Collapse,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Stack,
  Toolbar,
  Typography,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import PeopleIcon from '@mui/icons-material/People';
import GroupWorkIcon from '@mui/icons-material/GroupWork';
import SettingsIcon from '@mui/icons-material/Settings';
import SupervisorAccountIcon from '@mui/icons-material/SupervisorAccount';
import MonitorHeartIcon from '@mui/icons-material/MonitorHeart';
import HubIcon from '@mui/icons-material/Hub';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import StorageIcon from '@mui/icons-material/Storage';
import FolderIcon from '@mui/icons-material/Folder';
import MemoryIcon from '@mui/icons-material/Memory';
import PlayCircleIcon from '@mui/icons-material/PlayCircle';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import UserMenu from './UserMenu.jsx';
import { authApi, isAuthenticated } from '../api/auth.js';
import { setAuthErrorHandler } from '../api/client.js';

const PRIMARY_NAV = [
  { label: 'New Swarm', path: '/', icon: AutoAwesomeIcon },
];

const ADVANCED_NAV = [
  { label: 'LLM Providers', path: '/llm-providers', icon: MemoryIcon },
  { label: 'Agents', path: '/agents', icon: PeopleIcon },
  { label: 'Repositories', path: '/repositories', icon: FolderIcon },
  { label: 'Swarms', path: '/swarms', icon: StorageIcon },
  { label: 'Monitor', path: '/monitor', icon: MonitorHeartIcon },
];

const LEGACY_NAV = [
  { label: 'Roles (Legacy)', path: '/roles', icon: PeopleIcon },
  { label: 'Compositions (Legacy)', path: '/compositions', icon: GroupWorkIcon },
];

const ADMIN_NAV = [
  { label: 'Users', path: '/users', icon: SupervisorAccountIcon },
  { label: 'Settings', path: '/settings', icon: SettingsIcon },
];

const ALL_ITEMS = [
  ...PRIMARY_NAV,
  ...ADVANCED_NAV,
  ...LEGACY_NAV,
  ...ADMIN_NAV,
];

const DRAWER_WIDTH = 264;

function NavSection({ title, items, active, onItemClick, collapsible = false, defaultOpen = true }) {
  const [open, setOpen] = useState(defaultOpen);

  const header = title && (
    <ListItemButton
      onClick={collapsible ? () => setOpen((o) => !o) : undefined}
      sx={{
        py: 0.5,
        mx: 1,
        borderRadius: 1,
        cursor: collapsible ? 'pointer' : 'default',
        '&:hover': collapsible ? undefined : { bgcolor: 'transparent' },
      }}
      disableRipple={!collapsible}
    >
      <ListItemText
        primary={title}
        primaryTypographyProps={{
          fontSize: '0.7rem',
          fontWeight: 700,
          letterSpacing: '0.08em',
          textTransform: 'uppercase',
          color: 'text.secondary',
        }}
      />
      {collapsible && (open ? <ExpandLessIcon fontSize="small" /> : <ExpandMoreIcon fontSize="small" />)}
    </ListItemButton>
  );

  const list = (
    <List disablePadding>
      {items.map((item) => {
        const Icon = item.icon;
        const isActive = active === item.path;
        return (
          <ListItem key={item.path} disablePadding>
            <ListItemButton
              component={Link}
              to={item.path}
              selected={isActive}
              onClick={onItemClick}
            >
              <ListItemIcon>
                <Icon fontSize="small" />
              </ListItemIcon>
              <ListItemText
                primary={item.label}
                primaryTypographyProps={{
                  fontSize: '0.9rem',
                  fontWeight: isActive ? 600 : 500,
                }}
              />
            </ListItemButton>
          </ListItem>
        );
      })}
    </List>
  );

  return (
    <Box sx={{ mb: 1 }}>
      {header}
      {collapsible ? <Collapse in={open}>{list}</Collapse> : list}
    </Box>
  );
}

export default function AppLayout({ children }) {
  const location = useLocation();
  const navigate = useNavigate();
  const theme = useTheme();
  const isDesktop = useMediaQuery(theme.breakpoints.up('md'));
  const [mobileOpen, setMobileOpen] = useState(false);
  const [authenticated, setAuthenticated] = useState(isAuthenticated());

  useEffect(() => {
    setAuthenticated(isAuthenticated());
    setAuthErrorHandler(() => setAuthenticated(false));
  }, []);

  const handleDrawerToggle = () => setMobileOpen((prev) => !prev);

  const handleLogout = async () => {
    await authApi.logout();
    setAuthenticated(false);
    navigate('/login');
  };

  const currentItem = ALL_ITEMS.find((item) => item.path === location.pathname);

  const brand = (
    <Stack direction="row" alignItems="center" spacing={1.5} sx={{ px: 2.5, py: 2 }}>
      <Box
        sx={{
          width: 36,
          height: 36,
          borderRadius: 2,
          display: 'grid',
          placeItems: 'center',
          background: (t) =>
            `linear-gradient(135deg, ${t.palette.primary.main} 0%, ${t.palette.secondary.main} 100%)`,
          color: 'common.white',
          boxShadow: (t) => `0 6px 16px ${t.palette.primary.main}33`,
        }}
      >
        <HubIcon fontSize="small" />
      </Box>
      <Box>
        <Typography variant="h6" sx={{ fontWeight: 700, lineHeight: 1 }}>
          Syntexa
        </Typography>
        <Typography variant="caption" color="text.secondary">
          Agent Swarm Platform
        </Typography>
      </Box>
    </Stack>
  );

  const itemClickHandler = () => {
    if (!isDesktop) setMobileOpen(false);
  };

  const drawerContent = (
    <Box
      sx={{
        width: DRAWER_WIDTH,
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {brand}
      <Divider />
      <Box sx={{ flex: 1, overflow: 'auto', py: 1 }}>
        <NavSection
          title="Create"
          items={PRIMARY_NAV}
          active={location.pathname}
          onItemClick={itemClickHandler}
        />
        <NavSection
          title="Advanced"
          items={ADVANCED_NAV}
          active={location.pathname}
          onItemClick={itemClickHandler}
          collapsible
          defaultOpen
        />
        <NavSection
          title="Legacy"
          items={LEGACY_NAV}
          active={location.pathname}
          onItemClick={itemClickHandler}
          collapsible
          defaultOpen={false}
        />
        <NavSection
          title="Admin"
          items={ADMIN_NAV}
          active={location.pathname}
          onItemClick={itemClickHandler}
          collapsible
          defaultOpen={false}
        />
      </Box>
      <Divider />
      <Box sx={{ p: 2 }}>
        <Typography variant="caption" color="text.secondary">
          v0.1.0 &middot; dev
        </Typography>
      </Box>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', bgcolor: 'background.default' }}>
      <AppBar
        position="fixed"
        sx={{
          width: { md: `calc(100% - ${DRAWER_WIDTH}px)` },
          ml: { md: `${DRAWER_WIDTH}px` },
        }}
      >
        <Toolbar sx={{ gap: 1 }}>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ display: { md: 'none' } }}
          >
            <MenuIcon />
          </IconButton>

          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="h6" noWrap sx={{ fontWeight: 600, lineHeight: 1.2 }}>
              {currentItem?.label || 'Syntexa'}
            </Typography>
            {currentItem && (
              <Typography variant="caption" color="text.secondary">
                {location.pathname}
              </Typography>
            )}
          </Box>

          {authenticated && <UserMenu onLogout={handleLogout} />}
        </Toolbar>
      </AppBar>

      <Box
        component="nav"
        sx={{ width: { md: DRAWER_WIDTH }, flexShrink: { md: 0 } }}
        aria-label="main navigation"
      >
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{ keepMounted: true }}
          sx={{
            display: { xs: 'block', md: 'none' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: DRAWER_WIDTH,
            },
          }}
        >
          {drawerContent}
        </Drawer>

        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', md: 'block' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: DRAWER_WIDTH,
            },
          }}
          open
        >
          {drawerContent}
        </Drawer>
      </Box>

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          width: { md: `calc(100% - ${DRAWER_WIDTH}px)` },
          px: { xs: 2, sm: 3, md: 4 },
          pt: { xs: 10, sm: 11 },
          pb: 6,
        }}
      >
        <Box sx={{ maxWidth: 1280, mx: 'auto' }}>{children}</Box>
      </Box>
    </Box>
  );
}
