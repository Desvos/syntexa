import React from 'react';

export default function HandoffTargets({ value = [], available = [], onChange, disabled }) {
  const toggle = (name) => {
    if (disabled) return;
    onChange(
      value.includes(name) ? value.filter((v) => v !== name) : [...value, name]
    );
  };

  if (available.length === 0) {
    return <p className="muted">No other roles to hand off to yet.</p>;
  }

  return (
    <div className="row" style={{ flexWrap: 'wrap' }} role="group" aria-label="handoff targets">
      {available.map((name) => {
        const checked = value.includes(name);
        return (
          <label key={name} className="row" style={{ gap: '0.25rem' }}>
            <input
              type="checkbox"
              checked={checked}
              onChange={() => toggle(name)}
              disabled={disabled}
              style={{ width: 'auto' }}
              aria-label={`handoff target ${name}`}
            />
            <span>{name}</span>
          </label>
        );
      })}
    </div>
  );
}
