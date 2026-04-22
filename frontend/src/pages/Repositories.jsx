import React, { useCallback, useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  IconButton,
  Stack,
  Switch,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Toolbar,
  Tooltip,
  Typography,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import RefreshIcon from '@mui/icons-material/Refresh';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import HelpOutlineIcon from '@mui/icons-material/HelpOutlined';
import { api } from '../api/client.js';

const EMPTY = {
  name: '',
  path: '',
  remote_url: '',
  default_branch: 'main',
  clickup_list_id: '',
  is_active: true,
};

export default function RepositoriesPage() {
  const [repositories, setRepositories] = useState([]);
  const [health, setHealth] = useState({}); // { [id]: {is_git_repo, path_exists, default_branch_exists} | 'loading' | 'error' }
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editorOpen, setEditorOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(EMPTY);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState(null);

  const loadHealth = useCallback(async (repos) => {
    const results = await Promise.all(
      repos.map(async (r) => {
        try {
          const h = await api.repositories.health(r.id);
          return [r.id, h];
        } catch {
          return [r.id, 'error'];
        }
      }),
    );
    setHealth(Object.fromEntries(results));
  }, []);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.repositories.list();
      const repos = data.repositories || [];
      setRepositories(repos);
      loadHealth(repos);
    } catch (err) {
      setError(err.message || 'Failed to load repositories.');
    } finally {
      setLoading(false);
    }
  }, [loadHealth]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  function openNew() {
    setEditing(null);
    setForm(EMPTY);
    setSaveError(null);
    setEditorOpen(true);
  }

  function openEdit(repo) {
    setEditing(repo);
    setForm({
      name: repo.name,
      path: repo.path,
      remote_url: repo.remote_url || '',
      default_branch: repo.default_branch,
      clickup_list_id: repo.clickup_list_id || '',
      is_active: repo.is_active,
    });
    setSaveError(null);
    setEditorOpen(true);
  }

  async function handleSave() {
    setSaving(true);
    setSaveError(null);
    try {
      if (editing) {
        const payload = {
          path: form.path,
          remote_url: form.remote_url || null,
          default_branch: form.default_branch,
          clickup_list_id: form.clickup_list_id || null,
          is_active: form.is_active,
        };
        await api.repositories.update(editing.id, payload);
      } else {
        await api.repositories.create({
          name: form.name,
          path: form.path,
          remote_url: form.remote_url || null,
          default_branch: form.default_branch,
          clickup_list_id: form.clickup_list_id || null,
          is_active: form.is_active,
        });
      }
      setEditorOpen(false);
      await refresh();
    } catch (err) {
      setSaveError(err.message || 'Save failed.');
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(repo) {
    if (!window.confirm(`Delete repository "${repo.name}"?`)) return;
    try {
      await api.repositories.remove(repo.id);
      await refresh();
    } catch (err) {
      setError(err.message || 'Delete failed.');
    }
  }

  function renderHealth(repoId) {
    const h = health[repoId];
    if (!h)
      return (
        <Tooltip title="Loading…">
          <HelpOutlineIcon fontSize="small" color="action" />
        </Tooltip>
      );
    if (h === 'error')
      return (
        <Tooltip title="Health check failed">
          <ErrorIcon fontSize="small" color="error" />
        </Tooltip>
      );
    const healthy = h.is_git_repo && h.path_exists && h.default_branch_exists;
    return (
      <Tooltip
        title={
          <Box>
            <div>path_exists: {String(h.path_exists)}</div>
            <div>is_git_repo: {String(h.is_git_repo)}</div>
            <div>default_branch_exists: {String(h.default_branch_exists)}</div>
          </Box>
        }
      >
        {healthy ? (
          <CheckCircleIcon fontSize="small" color="success" />
        ) : (
          <ErrorIcon fontSize="small" color="warning" />
        )}
      </Tooltip>
    );
  }

  return (
    <Box>
      <Box sx={{ mb: 2 }}>
        <Typography variant="h4" component="h1" sx={{ fontWeight: 600 }}>
          Repositories
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Code repositories the daemon may bind worktrees to. Rows can exist before the path is
          materialized.
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Toolbar sx={{ justifyContent: 'space-between', px: 0, mb: 2 }}>
        <Typography variant="h6">All repositories</Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title="Refresh">
            <IconButton onClick={refresh} disabled={loading}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          <Button variant="contained" startIcon={<AddIcon />} onClick={openNew}>
            New Repository
          </Button>
        </Box>
      </Toolbar>

      <Card variant="outlined">
        <CardContent sx={{ p: 0 }}>
          {loading ? (
            <Box sx={{ p: 4, textAlign: 'center' }}>
              <CircularProgress size={24} />
            </Box>
          ) : repositories.length === 0 ? (
            <Box sx={{ p: 3, textAlign: 'center' }}>
              <Typography color="text.secondary">No repositories yet.</Typography>
            </Box>
          ) : (
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Health</TableCell>
                  <TableCell>Name</TableCell>
                  <TableCell>Path</TableCell>
                  <TableCell>Default branch</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {repositories.map((r) => (
                  <TableRow key={r.id} hover>
                    <TableCell>{renderHealth(r.id)}</TableCell>
                    <TableCell>{r.name}</TableCell>
                    <TableCell>
                      <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>
                        {r.path}
                      </Typography>
                    </TableCell>
                    <TableCell>{r.default_branch}</TableCell>
                    <TableCell>
                      <Chip
                        label={r.is_active ? 'active' : 'disabled'}
                        size="small"
                        color={r.is_active ? 'success' : 'default'}
                        variant={r.is_active ? 'filled' : 'outlined'}
                      />
                    </TableCell>
                    <TableCell align="right">
                      <IconButton size="small" onClick={() => openEdit(r)} aria-label="edit">
                        <EditIcon fontSize="small" />
                      </IconButton>
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => handleDelete(r)}
                        aria-label="delete"
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Dialog open={editorOpen} onClose={() => setEditorOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>{editing ? `Edit ${editing.name}` : 'New repository'}</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            {saveError && <Alert severity="error">{saveError}</Alert>}
            {!editing && (
              <TextField
                label="Name"
                value={form.name}
                onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                helperText="Short slug. Not editable later."
                required
              />
            )}
            <TextField
              label="Absolute path"
              value={form.path}
              onChange={(e) => setForm((f) => ({ ...f, path: e.target.value }))}
              required
              placeholder="/home/you/code/my-project"
            />
            <TextField
              label="Remote URL (optional)"
              value={form.remote_url}
              onChange={(e) => setForm((f) => ({ ...f, remote_url: e.target.value }))}
            />
            <TextField
              label="Default branch"
              value={form.default_branch}
              onChange={(e) => setForm((f) => ({ ...f, default_branch: e.target.value }))}
              required
            />
            <TextField
              label="ClickUp list id (optional)"
              value={form.clickup_list_id}
              onChange={(e) =>
                setForm((f) => ({ ...f, clickup_list_id: e.target.value }))
              }
            />
            <FormControlLabel
              control={
                <Switch
                  checked={form.is_active}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, is_active: e.target.checked }))
                  }
                />
              }
              label="Active"
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditorOpen(false)} disabled={saving}>
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={handleSave}
            disabled={
              saving ||
              !form.path.trim() ||
              !form.default_branch.trim() ||
              (!editing && !form.name.trim())
            }
          >
            {saving ? 'Saving…' : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
