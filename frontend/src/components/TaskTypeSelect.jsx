import React from 'react';

// Keep in sync with backend VALID_TASK_TYPES / daemon.classifier.TASK_TYPE_KEYWORDS.
export const TASK_TYPES = ['feature', 'fix', 'refactor', 'security', 'chore'];

export default function TaskTypeSelect({ value, onChange, disabled, exclude = [] }) {
  // `exclude` hides task types already bound to another composition — the
  // backend enforces uniqueness, but the picker shouldn't tempt users into
  // a 409.
  const options = TASK_TYPES.filter((t) => !exclude.includes(t) || t === value);

  return (
    <select
      aria-label="task type"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      disabled={disabled}
      required
    >
      <option value="" disabled>
        Select task type…
      </option>
      {options.map((t) => (
        <option key={t} value={t}>{t}</option>
      ))}
    </select>
  );
}
