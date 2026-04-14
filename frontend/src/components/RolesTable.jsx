import React from 'react';

export default function RolesTable({ roles, onEdit, onDelete, busyId }) {
  if (roles.length === 0) {
    return <p className="muted">No roles yet. Create one to get started.</p>;
  }

  return (
    <table>
      <thead>
        <tr>
          <th>Name</th>
          <th>Handoff targets</th>
          <th>Default</th>
          <th aria-label="actions" />
        </tr>
      </thead>
      <tbody>
        {roles.map((role) => {
          const busy = busyId === role.id;
          return (
            <tr key={role.id} data-testid={`role-row-${role.name}`}>
              <td><strong>{role.name}</strong></td>
              <td>
                {role.handoff_targets.length === 0
                  ? <span className="muted">—</span>
                  : role.handoff_targets.join(', ')}
              </td>
              <td>
                {role.is_default ? <span className="badge">default</span> : ''}
              </td>
              <td>
                <div className="row" style={{ justifyContent: 'flex-end' }}>
                  <button onClick={() => onEdit(role)} disabled={busy}>
                    Edit
                  </button>
                  <button
                    className="danger"
                    onClick={() => onDelete(role)}
                    disabled={busy || role.is_default}
                    title={role.is_default ? 'Default roles cannot be deleted' : undefined}
                  >
                    Delete
                  </button>
                </div>
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
