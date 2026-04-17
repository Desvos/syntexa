import React from 'react';
import {
  FormControl,
  InputLabel,
  MenuItem,
  Select,
} from '@mui/material';

// Keep in sync with backend VALID_TASK_TYPES / daemon.classifier.TASK_TYPE_KEYWORDS.
export const TASK_TYPES = ['feature', 'fix', 'refactor', 'security', 'chore'];

/**
 * TaskTypeSelect - MUI Select for task type
 *
 * Features:
 * - Styled Select component
 * - Excludes already bound task types
 * - Disabled state support
 */
export default function TaskTypeSelect({ value, onChange, disabled, exclude = [] }) {
  // `exclude` hides task types already bound to another composition — the
  // backend enforces uniqueness, but the picker shouldn't tempt users into
  // a 409.
  const options = TASK_TYPES.filter((t) => !exclude.includes(t) || t === value);

  return (
    <FormControl fullWidth disabled={disabled}>
      <InputLabel id="task-type-label">Task Type</InputLabel>
      <Select
        labelId="task-type-label"
        id="task-type"
        value={value}
        label="Task Type"
        onChange={(e) => onChange(e.target.value)}
        required
      >
        <MenuItem value="" disabled>
          <em>Select task type…</em>
        </MenuItem>
        {options.map((t) => (
          <MenuItem key={t} value={t} sx={{ textTransform: 'capitalize' }}>
            {t}
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
}
