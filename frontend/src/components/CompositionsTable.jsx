import React from 'react';
import {
  Box,
  Chip,
  IconButton,
  Tooltip,
} from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';

/**
 * CompositionsTable - MUI DataGrid-based compositions table
 *
 * Features:
 * - Task type with distinct styling
 * - Roles displayed as chips with arrows
 * - Edit/Delete actions
 */
export default function CompositionsTable({ compositions, onEdit, onDelete, busyId }) {
  const handleEdit = (composition) => {
    onEdit(composition);
  };

  const handleDelete = (composition) => {
    onDelete(composition);
  };

  const columns = [
    {
      field: 'task_type',
      headerName: 'Task Type',
      flex: 1,
      minWidth: 150,
      sortable: true,
      renderCell: (params) => (
        <Box sx={{ fontWeight: 600, textTransform: 'capitalize' }}>
          {params.value}
        </Box>
      ),
    },
    {
      field: 'roles',
      headerName: 'Roles (in order)',
      flex: 2,
      minWidth: 300,
      sortable: false,
      renderCell: (params) => {
        const roles = params.value || [];
        if (roles.length === 0) {
          return <Box sx={{ color: 'text.secondary', fontStyle: 'italic' }}>—</Box>;
        }
        return (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, flexWrap: 'wrap' }}>
            {roles.map((role, index) => (
              <Box key={role} sx={{ display: 'flex', alignItems: 'center' }}>
                <Chip
                  label={role}
                  size="small"
                  variant={index === 0 ? 'filled' : 'outlined'}
                  color={index === 0 ? 'primary' : 'default'}
                />
                {index < roles.length - 1 && (
                  <ArrowForwardIcon sx={{ fontSize: 16, mx: 0.5, color: 'text.secondary' }} />
                )}
              </Box>
            ))}
          </Box>
        );
      },
    },
    {
      field: 'max_rounds',
      headerName: 'Max Rounds',
      width: 120,
      sortable: true,
      align: 'center',
      headerAlign: 'center',
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 120,
      sortable: false,
      filterable: false,
      renderCell: (params) => {
        const composition = params.row;
        const busy = busyId === composition.id;

        return (
          <Box sx={{ display: 'flex', gap: 0.5 }}>
            <Tooltip title="Edit composition">
              <IconButton
                size="small"
                color="primary"
                onClick={() => handleEdit(composition)}
                disabled={busy}
              >
                <EditIcon fontSize="small" />
              </IconButton>
            </Tooltip>

            <Tooltip title="Delete composition">
              <IconButton
                size="small"
                color="error"
                onClick={() => handleDelete(composition)}
                disabled={busy}
              >
                <DeleteIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </Box>
        );
      },
    },
  ];

  const rows = React.useMemo(() => {
    return compositions.map((comp) => ({
      id: comp.id,
      task_type: comp.task_type,
      roles: comp.roles || [],
      max_rounds: comp.max_rounds,
    }));
  }, [compositions]);

  if (compositions.length === 0) {
    return (
      <Box
        sx={{
          p: 4,
          textAlign: 'center',
          color: 'text.secondary',
          bgcolor: 'background.paper',
          borderRadius: 1,
        }}
      >
        No compositions yet. Create one to map a task type to a role pipeline.
      </Box>
    );
  }

  return (
    <Box sx={{ height: 400, width: '100%' }}>
      <DataGrid
        rows={rows}
        columns={columns}
        initialState={{
          pagination: {
            paginationModel: { pageSize: 10, page: 0 },
          },
        }}
        pageSizeOptions={[10, 25, 50]}
        disableRowSelectionOnClick
        loading={false}
        density="comfortable"
        sx={{
          border: 1,
          borderColor: 'divider',
          borderRadius: 1,
          '& .MuiDataGrid-cell:focus': {
            outline: 'none',
          },
        }}
      />
    </Box>
  );
}
