import React, { useState } from 'react';
import {
  Box,
  Button,
  Chip,
  FormControl,
  IconButton,
  InputLabel,
  List,
  ListItem,
  MenuItem,
  Paper,
  Select,
  Tooltip,
  Typography,
} from '@mui/material';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';

/**
 * Drag-to-reorder list of role names with MUI.
 *
 * Duplicates are intentionally allowed — e.g. the refactor default has two
 * coders for parallel work. Each row carries its own list index as the React key
 * so duplicates don't collide.
 *
 * Uses keyboard controls (up/down arrows) instead of drag for simplicity.
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

  const add = () => {
    if (!pickerValue) return;
    onChange([...value, pickerValue]);
    setPickerValue('');
  };

  const availableOptions = available.filter((a) => !value.includes(a));

  return (
    <Box aria-label="role order">
      {/* Current order list */}
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
                  pr: 14, // Make room for buttons
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

      {/* Add role controls */}
      <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-start' }}>
        <FormControl fullWidth size="small">
          <InputLabel id="add-role-label">Add Role</InputLabel>
          <Select
            labelId="add-role-label"
            id="add-role"
            value={pickerValue}
            label="Add Role"
            onChange={(e) => setPickerValue(e.target.value)}
            disabled={disabled || availableOptions.length === 0}
          >
            <MenuItem value="" disabled>
              {availableOptions.length === 0 ? 'No roles available' : 'Select role...'}
            </MenuItem>
            {availableOptions.map((name) => (
              <MenuItem key={name} value={name}>{name}</MenuItem>
            ))}
          </Select>
        </FormControl>

        <Button
          variant="outlined"
          size="small"
          onClick={add}
          disabled={disabled || !pickerValue}
          startIcon={<AddIcon />}
          sx={{ mt: 0.5 }}
        >
          Add
        </Button>
      </Box>
    </Box>
  );
}
