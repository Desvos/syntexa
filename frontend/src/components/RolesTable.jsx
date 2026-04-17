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
import VerifiedIcon from '@mui/icons-material/Verified';

/**
 * RolesTable - MUI DataGrid-based roles table
 *
 * Features:
 * - Sorting, pagination
 * - Chip for handoff targets
 * - Badge for default roles
 * - Edit/Delete actions
 */
export default function RolesTable({ roles, onEdit, onDelete, busyId }) {
  const handleEdit = (role) => {
    onEdit(role);
  };

  const handleDelete = (role) => {
    onDelete(role);
  };

  const columns = [
    {
      field: 'name',
      headerName: 'Name',
      flex: 1,
      minWidth: 150,
      sortable: true,
      renderCell: (params) => (
        <Box sx={{ fontWeight: 600 }}>{params.value}</Box>
      ),
    },
    {
      field: 'handoff_targets',
      headerName: 'Handoff Targets',
      flex: 2,
      minWidth: 200,
      sortable: false,
      renderCell: (params) => {
        const targets = params.value || [];
        if (targets.length === 0) {
          return (
            <Box sx={{ color: 'text.secondary', fontStyle: 'italic' }}>
              —
            </Box>
          );
        }
        return (
          <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
            {targets.map((target) => (
              <Chip
                key={target}
                label={target}
                size="small"
                variant="outlined"
                color="primary"
              />
            ))}
          </Box>
        );
      },
    },
    {
      field: 'is_default',
      headerName: 'Default',
      width: 100,
      sortable: true,
      align: 'center',
      headerAlign: 'center',
      renderCell: (params) => {
        if (params.value) {
          return (
            <Tooltip title="Default role - cannot delete">
              <Chip
                icon={<VerifiedIcon fontSize="small" />}
                label="default"
                size="small"
                color="success"
              />
            </Tooltip>
          );
        }
        return <Box>—</Box>;
      },
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 120,
      sortable: false,
      filterable: false,
      renderCell: (params) => {
        const role = params.row;
        const busy = busyId === role.id;
        const isDefault = role.is_default;

        return (
          <Box sx={{ display: 'flex', gap: 0.5 }}>
            <Tooltip title="Edit role">
              <IconButton
                size="small"
                color="primary"
                onClick={() => handleEdit(role)}
                disabled={busy}
              >
                <EditIcon fontSize="small" />
              </IconButton>
            </Tooltip>

            <Tooltip
              title={
                isDefault ? "Default roles cannot be deleted" : "Delete role"
              }
            >
              <span>
                <IconButton
                  size="small"
                  color="error"
                  onClick={() => handleDelete(role)}
                  disabled={busy || isDefault}
                >
                  <DeleteIcon fontSize="small" />
                </IconButton>
              </span>
            </Tooltip>
          </Box>
        );
      },
    },
  ];

  const rows = React.useMemo(() => {
    return roles.map((role) => ({
      id: role.id,
      name: role.name,
      handoff_targets: role.handoff_targets || [],
      is_default: role.is_default,
    }));
  }, [roles]);

  if (roles.length === 0) {
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
        No roles yet. Create one to get started.
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
