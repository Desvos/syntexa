import React, { useCallback, useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  IconButton,
  Toolbar,
  Tooltip,
  Typography,
  Skeleton,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import RefreshIcon from '@mui/icons-material/Refresh';
import { api, ApiError } from '../api/client.js';
import RoleEditor from '../components/RoleEditor.jsx';
import RolesTable from '../components/RolesTable.jsx';

/**
 * RolesPage - Agent roles management page with MUI components
 *
 * Features:
 * - DataGrid table with sorting
 * - Create/Edit role dialog
 * - Delete role with confirmation
 * - Refresh button
 */
export default function RolesPage() {
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editing, setEditing] = useState(null); // null | 'new' | roleObject
  const [busyId, setBusyId] = useState(null);
  const [editorOpen, setEditorOpen] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.roles.list();
      setRoles(data.roles);
    } catch (err) {
      setError(err.message || 'Could not load roles.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  async function handleSave(payload) {
    if (editing === 'new') {
      await api.roles.create(payload);
    } else {
      await api.roles.update(editing.id, payload);
    }
    setEditing(null);
    setEditorOpen(false);
    await refresh();
  }

  async function handleDelete(role) {
    if (!window.confirm(`Delete role "${role.name}"?`)) return;
    setBusyId(role.id);
    setError(null);
    try {
      await api.roles.remove(role.id);
      await refresh();
    } catch (err) {
      // Most common 409: role used by a composition. Surface detail.
      const msg = err instanceof ApiError ? err.message : 'Delete failed.';
      setError(msg);
    } finally {
      setBusyId(null);
    }
  }

  const handleNewRole = () => {
    setEditing('new');
    setEditorOpen(true);
  };

  const handleEditRole = (role) => {
    setEditing(role);
    setEditorOpen(true);
  };

  const handleCloseEditor = () => {
    setEditorOpen(false);
    setEditing(null);
  };

  return (
    <Box sx={{ width: '100%' }}>
      {/* Header */}
      <Box sx={{ mb: 2 }}>
        <Typography variant="h4" component="h1" sx={{ fontWeight: 500, mb: 1 }}>
          Agent Roles
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Custom roles drive swarm behavior. Default roles can be edited but not deleted.
        </Typography>
      </Box>

      {/* Error */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Toolbar */}
      <Toolbar sx={{ justifyContent: 'space-between', px: 0, mb: 2 }}>
        <Typography variant="h6" component="h2">
          All Roles
        </Typography>

        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title="Refresh roles">
            <IconButton onClick={refresh} disabled={loading}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>

          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleNewRole}
          >
            New Role
          </Button>
        </Box>
      </Toolbar>

      {/* Content */}
      <Card variant="outlined">
        <CardContent sx={{ p: 0 }}>
          {loading ? (
            <Box sx={{ p: 2 }}>
              <Skeleton variant="rectangular" height={400} />
            </Box>
          ) : (
            <RolesTable
              roles={roles}
              onEdit={handleEditRole}
              onDelete={handleDelete}
              busyId={busyId}
            />
          )}
        </CardContent>
      </Card>

      {/* Role Editor Dialog */}
      <RoleEditor
        open={editorOpen}
        onClose={handleCloseEditor}
        role={editing === 'new' ? null : editing}
        existingRoles={roles}
        onSave={handleSave}
        onCancel={handleCloseEditor}
      />
    </Box>
  );
}
