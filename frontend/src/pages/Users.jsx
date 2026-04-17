import React, { useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  TextField,
  Toolbar,
  Typography,
  Tooltip,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import RefreshIcon from '@mui/icons-material/Refresh';
import { usersApi } from '../api/auth.js';
import UsersTable from '../components/UsersTable.jsx';

/**
 * UsersPage - User management page with MUI components
 *
 * Features:
 * - DataGrid table with sorting, pagination
 * - Create user dialog with form validation
 * - Refresh button to reload users
 * - Alert for errors
 */
export default function UsersPage() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [newUser, setNewUser] = useState({ username: '', password: '' });
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState('');

  // Fetch users on mount
  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await usersApi.list();
      setUsers(data.users || []);
    } catch (err) {
      setError('Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setCreating(true);
    setCreateError('');

    try {
      await usersApi.create(newUser.username, newUser.password);
      setNewUser({ username: '', password: '' });
      setShowCreateDialog(false);
      await loadUsers();
    } catch (err) {
      setCreateError(err.message || 'Failed to create user');
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id) => {
    await usersApi.remove(id);
    await loadUsers();
  };

  const handleOpenDialog = () => {
    setShowCreateDialog(true);
    setCreateError('');
  };

  const handleCloseDialog = () => {
    setShowCreateDialog(false);
    setNewUser({ username: '', password: '' });
    setCreateError('');
  };

  return (
    <Box sx={{ width: '100%' }}>
      {/* Header */}
      <Toolbar sx={{ justifyContent: 'space-between', px: 0, mb: 2 }}>
        <Typography variant="h4" component="h1" sx={{ fontWeight: 500 }}>
          User Management
        </Typography>

        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title="Refresh users">
            <IconButton onClick={loadUsers} disabled={loading}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>

          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleOpenDialog}
          >
            Create User
          </Button>
        </Box>
      </Toolbar>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {/* Users Table */}
      <Card variant="outlined">
        <CardContent sx={{ p: 0 }}>
          <UsersTable
            users={users}
            onDelete={handleDelete}
            loading={loading}
          />
        </CardContent>
      </Card>

      {/* Create User Dialog */}
      <Dialog
        open={showCreateDialog}
        onClose={handleCloseDialog}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Create New User</DialogTitle>

        <form onSubmit={handleCreate}>
          <DialogContent>
            {createError && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {createError}
              </Alert>
            )}

            <TextField
              autoFocus
              fullWidth
              required
              id="new-username"
              label="Username"
              value={newUser.username}
              onChange={(e) =>
                setNewUser((u) => ({ ...u, username: e.target.value }))
              }
              margin="normal"
              placeholder="Enter username"
              inputProps={{ minLength: 3 }}
              helperText="At least 3 characters"
            />

            <TextField
              fullWidth
              required
              id="new-password"
              label="Password"
              type="password"
              value={newUser.password}
              onChange={(e) =>
                setNewUser((u) => ({ ...u, password: e.target.value }))
              }
              margin="normal"
              placeholder="Enter password"
              inputProps={{ minLength: 8 }}
              helperText="At least 8 characters"
            />
          </DialogContent>

          <DialogActions>
            <Button onClick={handleCloseDialog}>Cancel</Button>
            <Button
              type="submit"
              variant="contained"
              disabled={
                creating || !newUser.username || !newUser.password}
            >
              {creating ? 'Creating...' : 'Create'}
            </Button>
          </DialogActions>
        </form>
      </Dialog>
    </Box>
  );
}
