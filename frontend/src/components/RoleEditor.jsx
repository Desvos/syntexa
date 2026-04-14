import React, { useEffect, useState } from 'react';
import HandoffTargets from './HandoffTargets.jsx';

const EMPTY = { name: '', system_prompt: '', handoff_targets: [] };

export default function RoleEditor({ role, existingRoles, onSave, onCancel }) {
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
    } catch (err) {
      setError(err.message || 'Save failed.');
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="stack" aria-label="role editor">
      <div>
        <div>Name</div>
        <input
          type="text"
          aria-label="Name"
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
          disabled={isEdit || saving}
          required
          maxLength={64}
          placeholder="e.g. security-auditor"
        />
        {isEdit && (
          <div className="muted" style={{ fontSize: '0.8rem' }}>
            Role name can't change — compositions reference roles by name.
          </div>
        )}
      </div>

      <div>
        <div>System prompt</div>
        <textarea
          aria-label="System prompt"
          value={form.system_prompt}
          onChange={(e) => setForm({ ...form, system_prompt: e.target.value })}
          disabled={saving}
          required
          placeholder="Describe the agent's responsibility and when it hands off."
        />
      </div>

      <div>
        <div>Handoff targets</div>
        <HandoffTargets
          value={form.handoff_targets}
          available={availableTargets}
          onChange={(v) => setForm({ ...form, handoff_targets: v })}
          disabled={saving}
        />
      </div>

      {error && <div className="error" role="alert">{error}</div>}

      <div className="row">
        <button type="submit" className="primary" disabled={saving}>
          {saving ? 'Saving…' : isEdit ? 'Save' : 'Create role'}
        </button>
        <button type="button" onClick={onCancel} disabled={saving}>
          Cancel
        </button>
      </div>
    </form>
  );
}

function roleToForm(role) {
  return {
    name: role.name,
    system_prompt: role.system_prompt,
    handoff_targets: role.handoff_targets ?? [],
  };
}
