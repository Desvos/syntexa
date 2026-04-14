import React, { useCallback, useEffect, useState } from 'react';

import { api, ApiError } from '../api/client.js';
import CompositionEditor from '../components/CompositionEditor.jsx';
import CompositionsTable from '../components/CompositionsTable.jsx';

export default function CompositionsPage() {
  const [compositions, setCompositions] = useState([]);
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editing, setEditing] = useState(null);
  const [busyId, setBusyId] = useState(null);

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

  return (
    <main>
      <h1>Swarm compositions</h1>
      <p className="muted">
        Bind a task type to an ordered role pipeline. The first role is the entry point.
      </p>

      {error && <div className="error" role="alert">{error}</div>}

      {editing ? (
        <section aria-label="composition editor">
          <h2>
            {editing === 'new'
              ? 'New composition'
              : `Edit: ${editing.task_type}`}
          </h2>
          <CompositionEditor
            composition={editing === 'new' ? null : editing}
            availableRoles={roleNames}
            existingTaskTypes={existingTaskTypes}
            onSave={handleSave}
            onCancel={() => setEditing(null)}
          />
        </section>
      ) : (
        <>
          <div className="row" style={{ justifyContent: 'space-between' }}>
            <h2>All compositions</h2>
            <button className="primary" onClick={() => setEditing('new')}>
              New composition
            </button>
          </div>
          {loading ? (
            <p className="muted">Loading…</p>
          ) : (
            <CompositionsTable
              compositions={compositions}
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
