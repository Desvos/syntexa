import React, { useState } from 'react';

/**
 * Drag-to-reorder list of role names.
 *
 * Duplicates are intentionally allowed — e.g. the refactor default has two
 * coders for parallel work (see syntexa.daemon.compositions). Each row
 * carries its own list index as the React key so duplicates don't collide.
 *
 * HTML5 drag-and-drop is used rather than a library to avoid a dep for a
 * single interaction. `data-testid="role-order-item"` + `aria-label` on the
 * up/down keyboard controls give tests deterministic handles.
 */
export default function RoleOrder({ value = [], available = [], onChange, disabled }) {
  const [dragIndex, setDragIndex] = useState(null);
  const [pickerValue, setPickerValue] = useState('');

  const move = (from, to) => {
    if (from === to || to < 0 || to >= value.length) return;
    const next = value.slice();
    const [item] = next.splice(from, 1);
    next.splice(to, 0, item);
    onChange(next);
  };

  const remove = (i) => {
    const next = value.slice();
    next.splice(i, 1);
    onChange(next);
  };

  const add = () => {
    if (!pickerValue) return;
    onChange([...value, pickerValue]);
    setPickerValue('');
  };

  return (
    <div className="stack" aria-label="role order">
      {value.length === 0 ? (
        <p className="muted">No roles yet. Add at least one — the first is the swarm entry point.</p>
      ) : (
        <ol style={{ listStyle: 'decimal', paddingLeft: '1.5rem' }}>
          {value.map((name, i) => (
            <li
              key={`${name}-${i}`}
              draggable={!disabled}
              data-testid="role-order-item"
              onDragStart={() => setDragIndex(i)}
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => {
                e.preventDefault();
                if (dragIndex !== null) move(dragIndex, i);
                setDragIndex(null);
              }}
              onDragEnd={() => setDragIndex(null)}
              style={{
                cursor: disabled ? 'default' : 'grab',
                opacity: dragIndex === i ? 0.5 : 1,
                padding: '0.25rem 0',
              }}
            >
              <div className="row" style={{ gap: '0.5rem', alignItems: 'center' }}>
                <span style={{ flex: 1 }}>{name}</span>
                <button
                  type="button"
                  onClick={() => move(i, i - 1)}
                  disabled={disabled || i === 0}
                  aria-label={`move ${name} up`}
                >
                  ↑
                </button>
                <button
                  type="button"
                  onClick={() => move(i, i + 1)}
                  disabled={disabled || i === value.length - 1}
                  aria-label={`move ${name} down`}
                >
                  ↓
                </button>
                <button
                  type="button"
                  className="danger"
                  onClick={() => remove(i)}
                  disabled={disabled}
                  aria-label={`remove ${name} at ${i}`}
                >
                  Remove
                </button>
              </div>
            </li>
          ))}
        </ol>
      )}

      <div className="row" style={{ gap: '0.5rem' }}>
        <select
          aria-label="add role"
          value={pickerValue}
          onChange={(e) => setPickerValue(e.target.value)}
          disabled={disabled || available.length === 0}
        >
          <option value="">
            {available.length === 0 ? 'No roles available' : 'Add role…'}
          </option>
          {available.map((name) => (
            <option key={name} value={name}>{name}</option>
          ))}
        </select>
        <button
          type="button"
          onClick={add}
          disabled={disabled || !pickerValue}
        >
          Add
        </button>
      </div>
    </div>
  );
}
