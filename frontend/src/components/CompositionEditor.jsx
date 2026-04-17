import React, { useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Slider,
  TextField,
  Typography,
} from '@mui/material';
import RoleOrder from './RoleOrder.jsx';
import TaskTypeSelect from './TaskTypeSelect.jsx';

const EMPTY = { task_type: '', roles: [], max_rounds: 60 };

/**
 * CompositionEditor - MUI-based composition editor dialog
 *
 * Features:
 * - Task type selector (disabled in edit mode)
 * - Role ordering with drag/drop or list
 * - Slider for max rounds
 * - Error display with Alert
 */
export default function CompositionEditor({
  open,
  onClose,
  composition,
  availableRoles,
  existingTaskTypes,
  onSave,
  onCancel,
}) {
  const isEdit = Boolean(composition);
  const [form, setForm] = useState(composition ? compToForm(composition) : EMPTY);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setForm(composition ? compToForm(composition) : EMPTY);
    setError(null);
  }, [composition, open]);

  const excludeTaskTypes = isEdit
    ? []
    : existingTaskTypes.filter((t) => t !== form.task_type);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    if (!isEdit && !form.task_type) {
      setError('Pick a task type.');
      return;
    }
    if (form.roles.length === 0) {
      setError('Add at least one role to the pipeline.');
      return;
    }
    setSaving(true);
    try {
      const payload = isEdit
        ? { roles: form.roles, max_rounds: Number(form.max_rounds) }
        : {
            task_type: form.task_type,
            roles: form.roles,
            max_rounds: Number(form.max_rounds),
          };
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

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>
        {isEdit ? `Edit Composition: ${composition.task_type}` : 'Create New Composition'}
      </DialogTitle>

      <form onSubmit={handleSubmit}>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          {/* Task Type */}
          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle2" gutterBottom>
              Task Type
            </Typography>
            <TaskTypeSelect
              value={form.task_type}
              onChange={(v) => setForm({ ...form, task_type: v })}
              disabled={isEdit || saving}
              exclude={excludeTaskTypes}
            />
            {isEdit && (
              <Typography variant="caption" color="text.secondary">
                Task type can't change — it's the daemon's lookup key.
              </Typography>
            )}
          </Box>

          {/* Role Pipeline */}
          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle2" gutterBottom>
              Role Pipeline
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Select and order roles for this task type. The first role is the entry point.
            </Typography>

            <RoleOrder
              value={form.roles}
              available={availableRoles}
              onChange={(v) => setForm({ ...form, roles: v })}
              disabled={saving}
            />
          </Box>

          {/* Max Rounds */}
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Max Rounds
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Slider
                value={form.max_rounds}
                onChange={(e, v) => setForm({ ...form, max_rounds: v })}
                disabled={saving}
                min={1}
                max={500}
                step={10}
                marks={[
                  { value: 1, label: '1' },
                  { value: 60, label: '60' },
                  { value: 120, label: '120' },
                  { value: 500, label: '500' },
                ]}
                valueLabelDisplay="auto"
                sx={{ flex: 1 }}
              />
              <TextField
                type="number"
                value={form.max_rounds}
                onChange={(e) => setForm({ ...form, max_rounds: parseInt(e.target.value) || 1 })}
                disabled={saving}
                inputProps={{ min: 1, max: 500 }}
                sx={{ width: 80 }}
                size="small"
              />
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
            disabled={saving || (!isEdit && !form.task_type) || form.roles.length === 0}
          >
            {saving ? 'Saving...' : isEdit ? 'Save Changes' : 'Create Composition'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}

function compToForm(comp) {
  return {
    task_type: comp.task_type,
    roles: comp.roles ?? [],
    max_rounds: comp.max_rounds,
  };
}
