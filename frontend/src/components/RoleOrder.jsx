import React, { useState } from 'react';
import {
  Autocomplete,
  Box,
  Chip,
  IconButton,
  List,
  ListItem,
  Paper,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';

/**
 * Ordered list of role names with free-form picker.
 *
 * Any agent-type name can be typed — existing roles are surfaced as suggestions
 * but the user is not constrained to them. Unknown names are auto-materialized
 * into AgentRole rows by the backend on save.
 *
 * Duplicates are intentionally allowed (e.g. two coders for parallel work);
 * the list index is the React key so duplicates don't collide.
 */
export default function RoleOrder({ value = [], available = [], onChange, disabled }) {
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

  const addName = (raw) => {
    const name = (raw || '').trim();
    if (!name) return;
    onChange([...value, name]);
    setPickerValue('');
  };

  return (
    <Box aria-label="role order">
      {value.length === 0 ? (
        <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic', py: 2 }}>
          No roles yet. Add at least one — the first is the swarm entry point.
        </Typography>
      ) : (
        <Paper variant="outlined" sx={{ mb: 2 }}>
          <List dense disablePadding>
            {value.map((name, i) => (
              <ListItem
                key={`${name}-${i}`}
                data-testid="role-order-item"
                divider={i < value.length - 1}
                secondaryAction={
                  <Box sx={{ display: 'flex', gap: 0.5 }}>
                    <Tooltip title={`Move ${name} up`}>
                      <span>
                        <IconButton
                          edge="end"
                          size="small"
                          onClick={() => move(i, i - 1)}
                          disabled={disabled || i === 0}
                          aria-label={`move ${name} up`}
                        >
                          <ArrowUpwardIcon fontSize="small" />
                        </IconButton>
                      </span>
                    </Tooltip>

                    <Tooltip title={`Move ${name} down`}>
                      <span>
                        <IconButton
                          edge="end"
                          size="small"
                          onClick={() => move(i, i + 1)}
                          disabled={disabled || i === value.length - 1}
                          aria-label={`move ${name} down`}
                        >
                          <ArrowDownwardIcon fontSize="small" />
                        </IconButton>
                      </span>
                    </Tooltip>

                    <Tooltip title={`Remove ${name}`}>
                      <IconButton
                        edge="end"
                        size="small"
                        color="error"
                        onClick={() => remove(i)}
                        disabled={disabled}
                        aria-label={`remove ${name} at ${i}`}
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </Box>
                }
                sx={{
                  pr: 14,
                  bgcolor: i === 0 ? 'action.selected' : 'inherit',
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Chip
                    label={`${i + 1}`}
                    size="small"
                    color={i === 0 ? 'primary' : 'default'}
                    sx={{ minWidth: 30 }}
                  />
                  <Typography sx={{ fontWeight: 500 }}>{name}</Typography>
                </Box>
              </ListItem>
            ))}
          </List>
        </Paper>
      )}

      <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-start' }}>
        <Autocomplete
          freeSolo
          fullWidth
          options={available}
          inputValue={pickerValue}
          onInputChange={(_, v) => setPickerValue(v)}
          value={null}
          onChange={(_, v) => {
            if (typeof v === 'string') addName(v);
          }}
          disabled={disabled}
          renderInput={(params) => (
            <TextField
              {...params}
              label="Add Role"
              placeholder="Type any agent type (e.g. planner, security-auditor, docs-writer)"
              helperText="Any name is valid — unknown types are created automatically on save."
              size="small"
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  addName(pickerValue);
                }
              }}
            />
          )}
        />
        <IconButton
          onClick={() => addName(pickerValue)}
          disabled={disabled || !pickerValue.trim()}
          color="primary"
          size="large"
          aria-label="add role"
        >
          <AddIcon />
        </IconButton>
      </Box>
    </Box>
  );
}
