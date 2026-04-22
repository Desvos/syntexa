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
  TextField,
  Typography,
  IconButton,
  Autocomplete,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';

const EMPTY = { name: '', system_prompt: '', handoff_targets: [] };

/**
 * RoleEditor - MUI-based role editor component
 *
 * Features:
 * - TextField for name (read-only in edit mode)
 * - Multiline TextField for system prompt with character counter
 * - Free-form handoff targets input (not tied to existing roles)
 * - Error display with Alert
 * - Loading state
 */
export default function RoleEditor({ role, existingRoles, onSave, onCancel, open, onClose }) {
  // `role` null → create mode; otherwise edit mode (name is read-only).
  const isEdit = Boolean(role);
  const [form, setForm] = useState(role ? roleToForm(role) : EMPTY);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);
  const [newTarget, setNewTarget] = useState('');

  useEffect(() => {
    setForm(role ? roleToForm(role) : EMPTY);
    setError(null);
    setNewTarget('');
  }, [role]);

  // Suggestions from existing roles, but user can add any target they want
  const targetSuggestions = existingRoles
    .map((r) => r.name)
    .filter((n) => n !== form.name && !form.handoff_targets.includes(n));

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

          {/* Handoff Targets - Free-form input */}
          <Box sx={{ mt: 3 }}>
            <Typography variant="subtitle2" gutterBottom>
              Handoff Targets
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Add any agent names this role can hand off to. Not limited to existing roles.
            </Typography>

            {/* Selected targets as chips */}
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
              {form.handoff_targets.length === 0 && (
                <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                  No handoff targets defined yet.
                </Typography>
              )}
              {form.handoff_targets.map((target) => (
                <Chip
                  key={target}
                  label={target}
                  color="primary"
                  size="small"
                  onDelete={saving ? undefined : () => {
                    setForm({
                      ...form,
                      handoff_targets: form.handoff_targets.filter((t) => t !== target)
                    });
                  }}
                />
              ))}
            </Box>

            {/* Add new target - any string is valid */}
            <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-start' }}>
              <Autocomplete
                freeSolo
                fullWidth
                options={targetSuggestions}
                inputValue={newTarget}
                onInputChange={(e, value) => setNewTarget(value)}
                value={null}
                onChange={(e, value) => {
                  if (value && typeof value === 'string' && value.trim()) {
                    const trimmed = value.trim();
                    if (!form.handoff_targets.includes(trimmed)) {
                      setForm({
                        ...form,
                        handoff_targets: [...form.handoff_targets, trimmed]
                      });
                    }
                    setNewTarget('');
                  }
                }}
                disabled={saving}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label="Add handoff target"
                    placeholder="Type any agent name (e.g., 'planner', 'security-auditor')"
                    helperText="You can add any name, even if that role doesn't exist yet"
                    size="small"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        const trimmed = newTarget.trim();
                        if (trimmed && !form.handoff_targets.includes(trimmed)) {
                          setForm({
                            ...form,
                            handoff_targets: [...form.handoff_targets, trimmed]
                          });
                          setNewTarget('');
                        }
                      }
                    }}
                  />
                )}
              />
              <IconButton
                onClick={() => {
                  const trimmed = newTarget.trim();
                  if (trimmed && !form.handoff_targets.includes(trimmed)) {
                    setForm({
                      ...form,
                      handoff_targets: [...form.handoff_targets, trimmed]
                    });
                    setNewTarget('');
                  }
                }}
                disabled={!newTarget.trim() || saving}
                color="primary"
                size="large"
              >
                <AddIcon />
              </IconButton>
            </Box>
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
