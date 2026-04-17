import React from 'react';
import {
  Box,
  Chip,
  FormControl,
  FormGroup,
  FormControlLabel,
  Switch,
  Typography,
} from '@mui/material';

/**
 * HandoffTargets - MUI-based multi-select for handoff targets
 *
 * Features:
 * - Toggle switches for each available role
 * - Selected roles displayed as chips
 * - Disabled state support
 */
export default function HandoffTargets({ value = [], available = [], onChange, disabled }) {
  const toggle = (name) => {
    if (disabled) return;
    onChange(
      value.includes(name) ? value.filter((v) => v !== name) : [...value, name]
    );
  };

  if (available.length === 0) {
    return (
      <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
        No other roles to hand off to yet.
      </Typography>
    );
  }

  return (
    <Box role="group" aria-label="handoff targets">
      {/* Selected targets as chips */}
      {value.length > 0 && (
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
          {value.map((name) => (
            <Chip
              key={name}
              label={name}
              color="primary"
              size="small"
              onDelete={disabled ? undefined : () => toggle(name)}
            />
          ))}
        </Box>
      )}

      {/* Toggle switches for available roles */}
      <FormControl component="fieldset" fullWidth>
        <FormGroup sx={{ flexDirection: 'row', flexWrap: 'wrap', gap: 2 }}>
          {available.map((name) => {
            const checked = value.includes(name);
            return (
              <FormControlLabel
                key={name}
                control={
                  <Switch
                    checked={checked}
                    onChange={() => toggle(name)}
                    disabled={disabled}
                    size="small"
                  />
                }
                label={name}
                sx={{
                  '& .MuiFormControlLabel-label': {
                    fontSize: '0.875rem',
                  },
                }}
              />
            );
          })}
        </FormGroup>
      </FormControl>
    </Box>
  );
}
