import React, { useCallback, useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  IconButton,
  Skeleton,
  Toolbar,
  Tooltip,
  Typography,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import RefreshIcon from '@mui/icons-material/Refresh';
import { api, ApiError } from '../api/client.js';
import CompositionEditor from '../components/CompositionEditor.jsx';
import CompositionsTable from '../components/CompositionsTable.jsx';

/**
 * CompositionsPage - Swarm compositions management page with MUI components
 *
 * Features:
 * - DataGrid table with sorting
 * - Create/Edit composition dialog
 * - Role ordering editor
 * - Max rounds slider
 */
export default function CompositionsPage() {
  const [compositions, setCompositions] = useState([]);
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editing, setEditing] = useState(null); // null | 'new' | compositionObject
  const [busyId, setBusyId] = useState(null);
  const [editorOpen, setEditorOpen] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // Compositions reference roles by name, so we fetch both and pass
      // the available role list into the editor.
      const [compsData, rolesData] = await Promise.all([
        api.compositions.list(),
        api.roles.list(),
      ]);
      setCompositions(compsData.compositions);
      setRoles(rolesData.roles);
    } catch (err) {
      setError(err.message || 'Could not load compositions.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  async function handleSave(payload) {
    if (editing === 'new') {
      await api.compositions.create(payload);
    } else {
      await api.compositions.update(editing.id, payload);
    }
    setEditing(null);
    setEditorOpen(false);
    await refresh();
  }

  async function handleDelete(comp) {
    if (!window.confirm(`Delete composition for "${comp.task_type}"?`)) return;
    setBusyId(comp.id);
    setError(null);
    try {
      await api.compositions.remove(comp.id);
      await refresh();
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : 'Delete failed.';
      setError(msg);
    } finally {
      setBusyId(null);
    }
  }

  const roleNames = roles.map((r) => r.name);
  const existingTaskTypes = compositions.map((c) => c.task_type);

  const handleNewComposition = () => {
    setEditing('new');
    setEditorOpen(true);
  };

  const handleEditComposition = (composition) => {
    setEditing(composition);
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
          Swarm Compositions
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Bind a task type to an ordered role pipeline. The first role is the entry point.
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
          All Compositions
        </Typography>

        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title="Refresh compositions">
            <IconButton onClick={refresh} disabled={loading}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>

          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleNewComposition}
          >
            New Composition
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
            <CompositionsTable
              compositions={compositions}
              onEdit={handleEditComposition}
              onDelete={handleDelete}
              busyId={busyId}
            />
          )}
        </CardContent>
      </Card>

      {/* Composition Editor Dialog */}
      <CompositionEditor
        open={editorOpen}
        onClose={handleCloseEditor}
        composition={editing === 'new' ? null : editing}
        availableRoles={roleNames}
        existingTaskTypes={existingTaskTypes}
        onSave={handleSave}
        onCancel={handleCloseEditor}
      />
    </Box>
  );
}
