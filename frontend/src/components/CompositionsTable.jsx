import React from 'react';

export default function CompositionsTable({ compositions, onEdit, onDelete, busyId }) {
  if (compositions.length === 0) {
    return (
      <p className="muted">
        No compositions yet. Create one to map a task type to a role pipeline.
      </p>
    );
  }

  return (
    <table>
      <thead>
        <tr>
          <th>Task type</th>
          <th>Roles (in order)</th>
          <th>Max rounds</th>
          <th aria-label="actions" />
        </tr>
      </thead>
      <tbody>
        {compositions.map((comp) => {
          const busy = busyId === comp.id;
          return (
            <tr key={comp.id} data-testid={`composition-row-${comp.task_type}`}>
              <td><strong>{comp.task_type}</strong></td>
              <td>
                {comp.roles.length === 0
                  ? <span className="muted">—</span>
                  : comp.roles.join(' → ')}
              </td>
              <td>{comp.max_rounds}</td>
              <td>
                <div className="row" style={{ justifyContent: 'flex-end' }}>
                  <button onClick={() => onEdit(comp)} disabled={busy}>
                    Edit
                  </button>
                  <button
                    className="danger"
                    onClick={() => onDelete(comp)}
                    disabled={busy}
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
