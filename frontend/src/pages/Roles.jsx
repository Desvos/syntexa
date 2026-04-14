import React, { useCallback, useEffect, useState } from 'react';

import { api, ApiError } from '../api/client.js';
import RoleEditor from '../components/RoleEditor.jsx';
import RolesTable from '../components/RolesTable.jsx';

export default function RolesPage() {
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editing, setEditing] = useState(null); // null | 'new' | roleObject
  const [busyId, setBusyId] = useState(null);

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

  return (
    <main>
      <h1>Agent roles</h1>
      <p className="muted">
        Custom roles drive swarm behavior. Default roles can be edited but not deleted.
      </p>

      {error && <div className="error" role="alert">{error}</div>}

      {editing ? (
        <section aria-label="role editor">
          <h2>{editing === 'new' ? 'New role' : `Edit: ${editing.name}`}</h2>
          <RoleEditor
            role={editing === 'new' ? null : editing}
            existingRoles={roles}
            onSave={handleSave}
            onCancel={() => setEditing(null)}
          />
        </section>
      ) : (
        <>
          <div className="row" style={{ justifyContent: 'space-between' }}>
            <h2>All roles</h2>
            <button className="primary" onClick={() => setEditing('new')}>
              New role
            </button>
          </div>
          {loading ? (
            <p className="muted">Loading…</p>
          ) : (
            <RolesTable
              roles={roles}
              onEdit={setEditing}
              onDelete={handleDelete}
              busyId={busyId}
            />
          )}
        </>
      )}
    </main>
  );
}
