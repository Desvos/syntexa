import React, { useEffect, useState } from 'react';

import RoleOrder from './RoleOrder.jsx';
import TaskTypeSelect from './TaskTypeSelect.jsx';

const EMPTY = { task_type: '', roles: [], max_rounds: 60 };

export default function CompositionEditor({
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
  }, [composition]);

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
    } catch (err) {
      setError(err.message || 'Save failed.');
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="stack" aria-label="composition editor">
      <div>
        <div>Task type</div>
        <TaskTypeSelect
          value={form.task_type}
          onChange={(v) => setForm({ ...form, task_type: v })}
          disabled={isEdit || saving}
          exclude={excludeTaskTypes}
        />
        {isEdit && (
          <div className="muted" style={{ fontSize: '0.8rem' }}>
            Task type can't change — it's the daemon's lookup key.
          </div>
        )}
      </div>

      <div>
        <div>Role pipeline</div>
        <RoleOrder
          value={form.roles}
          available={availableRoles}
          onChange={(v) => setForm({ ...form, roles: v })}
          disabled={saving}
        />
      </div>

      <div>
        <div>Max rounds</div>
        <input
          type="number"
          aria-label="Max rounds"
          min={1}
          max={500}
          value={form.max_rounds}
          onChange={(e) => setForm({ ...form, max_rounds: e.target.value })}
          disabled={saving}
          required
        />
      </div>

      {error && <div className="error" role="alert">{error}</div>}

      <div className="row">
        <button type="submit" className="primary" disabled={saving}>
          {saving ? 'Saving…' : isEdit ? 'Save' : 'Create composition'}
        </button>
        <button type="button" onClick={onCancel} disabled={saving}>
          Cancel
        </button>
      </div>
    </form>
  );
}

function compToForm(comp) {
  return {
    task_type: comp.task_type,
    roles: comp.roles ?? [],
    max_rounds: comp.max_rounds,
  };
}
