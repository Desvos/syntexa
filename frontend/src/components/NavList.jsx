import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import PeopleIcon from '@mui/icons-material/People';
import GroupWorkIcon from '@mui/icons-material/GroupWork';
import SettingsIcon from '@mui/icons-material/Settings';
import SupervisorAccountIcon from '@mui/icons-material/SupervisorAccount';
import MonitorIcon from '@mui/icons-material/Monitor';

// Navigation items configuration
const NAV_ITEMS = [
  { label: 'Agent Roles', path: '/roles', icon: PeopleIcon },
  { label: 'Compositions', path: '/compositions', icon: GroupWorkIcon },
  { label: 'Monitor', path: '/monitor', icon: MonitorIcon },
  { label: 'Users', path: '/users', icon: SupervisorAccountIcon },
  { label: 'Settings', path: '/settings', icon: SettingsIcon },
];

/**
 * NavList - Navigation list component using MUI List
 *
 * Used in the sidebar drawer for navigation between pages.
 * Highlights the currently active route.
 */
export default function NavList({ onItemClick }) {
  const location = useLocation();

  return (
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
              onClick={onItemClick}
              sx={{
                '&.Mui-selected': {
                  backgroundColor: 'action.selected',
                },
                '&.Mui-selected:hover': {
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
  );
}
