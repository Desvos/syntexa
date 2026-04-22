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
import { api } from '../api/client.js';

const EMPTY = {
  name: '',
  system_prompt: '',
  provider_id: '',
  model: '',
  is_active: true,
};

function truncate(text, length = 80) {
  if (!text) return '';
  return text.length > length ? `${text.slice(0, length)}…` : text;
}

export default function AgentsPage() {
  const [agents, setAgents] = useState([]);
  const [providers, setProviders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editorOpen, setEditorOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(EMPTY);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [agentData, providerData] = await Promise.all([
        api.agents.list(),
        api.llmProviders.list(),
      ]);
      setAgents(agentData.agents || []);
      setProviders(providerData.providers || []);
    } catch (err) {
      setError(err.message || 'Failed to load agents.');
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

  function openEdit(agent) {
    setEditing(agent);
    setForm({
      name: agent.name,
      system_prompt: agent.system_prompt,
      provider_id: agent.provider_id,
      model: agent.model || '',
      is_active: agent.is_active,
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
          system_prompt: form.system_prompt,
          provider_id: Number(form.provider_id),
          model: form.model || null,
          is_active: form.is_active,
        };
        await api.agents.update(editing.id, payload);
      } else {
        const payload = {
          name: form.name,
          system_prompt: form.system_prompt,
          provider_id: Number(form.provider_id),
          model: form.model || null,
          is_active: form.is_active,
        };
        await api.agents.create(payload);
      }
      setEditorOpen(false);
      await refresh();
    } catch (err) {
      setSaveError(err.message || 'Save failed.');
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(agent) {
    if (!window.confirm(`Delete agent "${agent.name}"?`)) return;
    try {
      await api.agents.remove(agent.id);
      await refresh();
    } catch (err) {
      setError(err.message || 'Delete failed.');
    }
  }

  function providerLabel(id) {
    const p = providers.find((pp) => pp.id === id);
    return p ? `${p.name} (${p.default_model})` : `#${id}`;
  }

  return (
    <Box>
      <Box sx={{ mb: 2 }}>
        <Typography variant="h4" component="h1" sx={{ fontWeight: 600 }}>
          Agents
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Reusable agents wired to an LLM provider. Swarms pick agents by id at build time.
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Toolbar sx={{ justifyContent: 'space-between', px: 0, mb: 2 }}>
        <Typography variant="h6">All agents</Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title="Refresh">
            <IconButton onClick={refresh} disabled={loading}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          <Button variant="contained" startIcon={<AddIcon />} onClick={openNew}>
            New Agent
          </Button>
        </Box>
      </Toolbar>

      <Card variant="outlined">
        <CardContent sx={{ p: 0 }}>
          {loading ? (
            <Box sx={{ p: 4, textAlign: 'center' }}>
              <CircularProgress size={24} />
            </Box>
          ) : agents.length === 0 ? (
            <Box sx={{ p: 3, textAlign: 'center' }}>
              <Typography color="text.secondary">No agents yet.</Typography>
            </Box>
          ) : (
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell>Provider</TableCell>
                  <TableCell>Model</TableCell>
                  <TableCell>System prompt</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {agents.map((a) => (
                  <TableRow key={a.id} hover>
                    <TableCell>{a.name}</TableCell>
                    <TableCell>{providerLabel(a.provider_id)}</TableCell>
                    <TableCell>
                      {a.model || <em style={{ opacity: 0.6 }}>inherit</em>}
                    </TableCell>
                    <TableCell sx={{ maxWidth: 320 }}>
                      <Typography
                        variant="body2"
                        color="text.secondary"
                        sx={{ fontSize: '0.8rem' }}
                      >
                        {truncate(a.system_prompt, 120)}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={a.is_active ? 'active' : 'disabled'}
                        size="small"
                        color={a.is_active ? 'success' : 'default'}
                        variant={a.is_active ? 'filled' : 'outlined'}
                      />
                    </TableCell>
                    <TableCell align="right">
                      <IconButton size="small" onClick={() => openEdit(a)} aria-label="edit">
                        <EditIcon fontSize="small" />
                      </IconButton>
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => handleDelete(a)}
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
        <DialogTitle>{editing ? `Edit ${editing.name}` : 'New agent'}</DialogTitle>
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
            <FormControl fullWidth required>
              <InputLabel id="provider-label">LLM provider</InputLabel>
              <Select
                labelId="provider-label"
                label="LLM provider"
                value={form.provider_id}
                onChange={(e) =>
                  setForm((f) => ({ ...f, provider_id: e.target.value }))
                }
              >
                {providers.map((p) => (
                  <MenuItem key={p.id} value={p.id}>
                    {p.name} ({p.provider_type} — {p.default_model})
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <TextField
              label="Model (optional override)"
              value={form.model}
              onChange={(e) => setForm((f) => ({ ...f, model: e.target.value }))}
              helperText="Leave blank to inherit provider default."
            />
            <TextField
              label="System prompt"
              multiline
              minRows={6}
              value={form.system_prompt}
              onChange={(e) =>
                setForm((f) => ({ ...f, system_prompt: e.target.value }))
              }
              required
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
              !form.system_prompt.trim() ||
              !form.provider_id ||
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
