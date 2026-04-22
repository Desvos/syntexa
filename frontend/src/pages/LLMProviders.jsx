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
  FormControl,
  FormControlLabel,
  IconButton,
  InputLabel,
  MenuItem,
  Select,
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
import { api, LLM_PROVIDER_TYPES } from '../api/client.js';

const EMPTY = {
  name: '',
  provider_type: 'anthropic',
  base_url: '',
  api_key: '',
  default_model: '',
  is_active: true,
};

export default function LLMProvidersPage() {
  const [providers, setProviders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editorOpen, setEditorOpen] = useState(false);
  const [editing, setEditing] = useState(null); // null=new or provider object
  const [form, setForm] = useState(EMPTY);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.llmProviders.list();
      setProviders(data.providers || []);
    } catch (err) {
      setError(err.message || 'Failed to load providers.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  function openNew() {
    setEditing(null);
    setForm(EMPTY);
    setSaveError(null);
    setEditorOpen(true);
  }

  function openEdit(provider) {
    setEditing(provider);
    setForm({
      name: provider.name,
      provider_type: provider.provider_type,
      base_url: provider.base_url || '',
      api_key: '', // never prefill
      default_model: provider.default_model,
      is_active: provider.is_active,
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
          base_url: form.base_url || null,
          default_model: form.default_model,
          is_active: form.is_active,
        };
        if (form.api_key) payload.api_key = form.api_key;
        await api.llmProviders.update(editing.id, payload);
      } else {
        const payload = {
          name: form.name,
          provider_type: form.provider_type,
          base_url: form.base_url || null,
          api_key: form.api_key || null,
          default_model: form.default_model,
          is_active: form.is_active,
        };
        await api.llmProviders.create(payload);
      }
      setEditorOpen(false);
      await refresh();
    } catch (err) {
      setSaveError(err.message || 'Save failed.');
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(provider) {
    if (!window.confirm(`Delete provider "${provider.name}"?`)) return;
    try {
      await api.llmProviders.remove(provider.id);
      await refresh();
    } catch (err) {
      setError(err.message || 'Delete failed.');
    }
  }

  return (
    <Box>
      <Box sx={{ mb: 2 }}>
        <Typography variant="h4" component="h1" sx={{ fontWeight: 600 }}>
          LLM Providers
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Credentials and default models for each LLM backend. API keys are encrypted at rest.
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Toolbar sx={{ justifyContent: 'space-between', px: 0, mb: 2 }}>
        <Typography variant="h6">All providers</Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title="Refresh">
            <IconButton onClick={refresh} disabled={loading}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          <Button variant="contained" startIcon={<AddIcon />} onClick={openNew}>
            New Provider
          </Button>
        </Box>
      </Toolbar>

      <Card variant="outlined">
        <CardContent sx={{ p: 0 }}>
          {loading ? (
            <Box sx={{ p: 4, textAlign: 'center' }}>
              <CircularProgress size={24} />
            </Box>
          ) : providers.length === 0 ? (
            <Box sx={{ p: 3, textAlign: 'center' }}>
              <Typography color="text.secondary">No providers yet.</Typography>
            </Box>
          ) : (
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Default model</TableCell>
                  <TableCell>API key</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {providers.map((p) => (
                  <TableRow key={p.id} hover>
                    <TableCell>{p.name}</TableCell>
                    <TableCell>
                      <Chip label={p.provider_type} size="small" />
                    </TableCell>
                    <TableCell>{p.default_model}</TableCell>
                    <TableCell>
                      <code>{p.api_key_preview || '—'}</code>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={p.is_active ? 'active' : 'disabled'}
                        size="small"
                        color={p.is_active ? 'success' : 'default'}
                        variant={p.is_active ? 'filled' : 'outlined'}
                      />
                    </TableCell>
                    <TableCell align="right">
                      <IconButton size="small" onClick={() => openEdit(p)} aria-label="edit">
                        <EditIcon fontSize="small" />
                      </IconButton>
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => handleDelete(p)}
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
        <DialogTitle>{editing ? `Edit ${editing.name}` : 'New provider'}</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            {saveError && <Alert severity="error">{saveError}</Alert>}
            {!editing && (
              <>
                <TextField
                  label="Name"
                  value={form.name}
                  onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                  helperText="Short slug (letters, numbers, dashes, underscores)."
                  required
                />
                <FormControl fullWidth>
                  <InputLabel id="ptype">Type</InputLabel>
                  <Select
                    labelId="ptype"
                    label="Type"
                    value={form.provider_type}
                    onChange={(e) =>
                      setForm((f) => ({ ...f, provider_type: e.target.value }))
                    }
                  >
                    {LLM_PROVIDER_TYPES.map((t) => (
                      <MenuItem key={t} value={t}>
                        {t}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </>
            )}
            <TextField
              label="Default model"
              value={form.default_model}
              onChange={(e) =>
                setForm((f) => ({ ...f, default_model: e.target.value }))
              }
              required
            />
            <TextField
              label="Base URL (optional)"
              value={form.base_url}
              onChange={(e) => setForm((f) => ({ ...f, base_url: e.target.value }))}
              placeholder="https://api.openai.com/v1"
            />
            <TextField
              label={editing ? 'API key (leave blank to keep existing)' : 'API key'}
              type="password"
              value={form.api_key}
              onChange={(e) => setForm((f) => ({ ...f, api_key: e.target.value }))}
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
          <Button variant="contained" onClick={handleSave} disabled={saving}>
            {saving ? 'Saving…' : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
