import React, { useState } from 'react';
import {
  Alert,
  Box,
  Chip,
  IconButton,
  Snackbar,
  Tooltip,
} from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import DeleteIcon from '@mui/icons-material/Delete';
import PersonIcon from '@mui/icons-material/Person';

/**
 * UsersTable - MUI DataGrid-based users table
 *
 * Features:
 * - Sorting, pagination out of the box
 * - Row selection with checkboxes
 * - Status chips
 * - Delete action buttons
 * - Loading state with skeleton
 */
export default function UsersTable({ users, currentUserId, onDelete, loading }) {
  const [deleting, setDeleting] = useState(null);
  const [error, setError] = useState('');
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });

  const handleDelete = async (id) => {
    if (id === currentUserId) {
      setError('Cannot delete your own account');
      return;
    }

    setDeleting(id);
    setError('');

    try {
      await onDelete(id);
      setSnackbar({ open: true, message: 'User deleted successfully', severity: 'success' });
    } catch (err) {
      setError(err.message || 'Failed to delete user');
      setSnackbar({ open: true, message: err.message || 'Failed to delete user', severity: 'error' });
    } finally {
      setDeleting(null);
    }
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  // Define columns for DataGrid
  const columns = [
    {
      field: 'id',
      headerName: 'ID',
      width: 70,
      sortable: true,
    },
    {
      field: 'username',
      headerName: 'Username',
      flex: 1,
      minWidth: 150,
      sortable: true,
      renderCell: (params) => (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <PersonIcon fontSize="small" color="action" />
          {params.value}
        </Box>
      ),
    },
    {
      field: 'created_at',
      headerName: 'Created',
      flex: 1,
      minWidth: 120,
      sortable: true,
      valueFormatter: (params) => {
        if (!params) return 'Unknown';
        return new Date(params).toLocaleDateString();
      },
    },
    {
      field: 'last_login_at',
      headerName: 'Last Login',
      flex: 1,
      minWidth: 120,
      sortable: true,
      renderCell: (params) => {
        const value = params.row.last_login_at;
        if (!value) {
          return (
            <Chip
              label="Never"
              size="small"
              variant="outlined"
              color="default"
            />
          );
        }
        return new Date(value).toLocaleDateString();
      },
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 100,
      sortable: false,
      filterable: false,
      renderCell: (params) => {
        const userId = params.row.id;
        const isCurrentUser = userId === currentUserId;
        const isDeleting = deleting === userId;

        return (
          <Tooltip
            title={isCurrentUser ? "Cannot delete your own account" : "Delete user"}
          >
            <span>
              <IconButton
                size="small"
                color="error"
                onClick={() => handleDelete(userId)}
                disabled={isCurrentUser || isDeleting}
                aria-label={isCurrentUser ? "Cannot delete own account" : "Delete user"}
              >
                <DeleteIcon fontSize="small" />
              </IconButton>
            </span>
          </Tooltip>
        );
      },
    },
  ];

  // Prepare rows for DataGrid
  const rows = React.useMemo(() => {
    return users.map(user => ({
      id: user.id,
      username: user.username,
      created_at: user.created_at,
      last_login_at: user.last_login_at,
    }));
  }, [users]);

  if (loading) {
    return (
      <Box sx={{ width: '100%', height: 400, bgcolor: 'background.paper', borderRadius: 1 }}>
        <DataGrid
          rows={[]}
          columns={columns}
          loading={true}
          disableRowSelectionOnClick
        />
      </Box>
    );
  }

  return (
    <Box sx={{ width: '100%' }}>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

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
          checkboxSelection
          disableRowSelectionOnClick
          loading={loading}
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

      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={handleCloseSnackbar}
          severity={snackbar.severity}
          variant="filled"
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}
