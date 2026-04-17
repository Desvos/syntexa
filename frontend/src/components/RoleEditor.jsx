import React, { useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  FormHelperText,
  InputLabel,
  MenuItem,
  OutlinedInput,
  Select,
  TextField,
  Typography,
} from '@mui/material';
import HandoffTargets from './HandoffTargets.jsx';

const EMPTY = { name: '', system_prompt: '', handoff_targets: [] };

/**
 * RoleEditor - MUI-based role editor component
 *
 * Features:
 * - TextField for name (read-only in edit mode)
 * - Multiline TextField for system prompt with character counter
 * - HandoffTargets selector for multi-select
 * - Error display with Alert
 * - Loading state
 */
export default function RoleEditor({ role, existingRoles, onSave, onCancel, open, onClose }) {
  // `role` null → create mode; otherwise edit mode (name is read-only).
  const isEdit = Boolean(role);
  const [form, setForm] = useState(role ? roleToForm(role) : EMPTY);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setForm(role ? roleToForm(role) : EMPTY);
    setError(null);
  }, [role]);

  const availableTargets = existingRoles
    .map((r) => r.name)
    .filter((n) => n !== form.name);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setSaving(true);
    try {
      const payload = isEdit
        ? { system_prompt: form.system_prompt, handoff_targets: form.handoff_targets }
        : form;
      await onSave(payload);
      onClose?.();
    } catch (err) {
      setError(err.message || 'Save failed.');
    } finally {
      setSaving(false);
    }
  }

  const handleClose = () => {
    if (!saving) {
      setError(null);
      onClose?.();
      onCancel?.();
    }
  };

  const promptCharCount = form.system_prompt?.length || 0;
  const promptMaxLength = 4000;

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>
        {isEdit ? `Edit Role: ${role.name}` : 'Create New Role'}
      </DialogTitle>

      <form onSubmit={handleSubmit}>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          {/* Name Field */}
          <TextField
            fullWidth
            required
            id="role-name"
            label="Role Name"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            disabled={isEdit || saving}
            placeholder="e.g. security-auditor"
            margin="normal"
            inputProps={{ maxLength: 64 }}
            helperText={
              isEdit
                ? "Role name cannot be changed — compositions reference roles by name."
                : "Choose a unique, descriptive name (max 64 characters)."
            }
          />

          {/* System Prompt */}
          <TextField
            fullWidth
            required
            multiline
            rows={6}
            id="system-prompt"
            label="System Prompt"
            value={form.system_prompt}
            onChange={(e) => setForm({ ...form, system_prompt: e.target.value })}
            disabled={saving}
            placeholder="Describe the agent's responsibility and when it hands off."
            margin="normal"
            helperText={
              <Box component="span" sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Describe the agent's responsibility</span>
                <Box component="span" sx={{ color: promptCharCount > promptMaxLength * 0.9 ? 'error.main' : 'text.secondary' }}>
                  {promptCharCount}/{promptMaxLength}
                </Box>
              </Box>
            }
          />

          {/* Handoff Targets */}
          <Box sx={{ mt: 3 }}>
            <Typography variant="subtitle2" gutterBottom>
              Handoff Targets
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Select which roles this agent can hand off to.
            </Typography>

            <HandoffTargets
              value={form.handoff_targets}
              available={availableTargets}
              onChange={(v) => setForm({ ...form, handoff_targets: v })}
              disabled={saving}
            />
          </Box>
        </DialogContent>

        <DialogActions>
          <Button onClick={handleClose} disabled={saving}>
            Cancel
          </Button>
          <Button
            type="submit"
            variant="contained"
            disabled={saving || !form.name || !form.system_prompt}
          >
            {saving ? 'Saving...' : isEdit ? 'Save Changes' : 'Create Role'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}

function roleToForm(role) {
  return {
    name: role.name,
    system_prompt: role.system_prompt,
    handoff_targets: role.handoff_targets ?? [],
  };
}
