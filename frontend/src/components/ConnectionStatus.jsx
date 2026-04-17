import React from 'react';
import {
  Alert,
  Box,
  Card,
  CardContent,
  CardHeader,
  Chip,
  Grid,
  Skeleton,
  Typography,
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import WarningIcon from '@mui/icons-material/Warning';
import HelpIcon from '@mui/icons-material/Help';

/**
 * ConnectionStatus - MUI Card displaying service connection statuses
 *
 * Features:
 * - Visual status chips with icons
 * - Color-coded: green (connected), red (error), orange (unconfigured)
 * - Service details in a grid layout
 */
export default function ConnectionStatus({ connections, loading }) {
  if (loading) {
    return (
      <Card variant="outlined">
        <CardHeader title="Connection Status" />
        <CardContent>
          <Skeleton variant="rectangular" height={100} />
        </CardContent>
      </Card>
    );
  }

  if (!connections || connections.length === 0) {
    return (
      <Card variant="outlined">
        <CardHeader title="Connection Status" />
        <CardContent>
          <Typography variant="body2" color="text.secondary">
            No connection data available.
          </Typography>
        </CardContent>
      </Card>
    );
  }

  const getStatusConfig = (status) => {
    switch (status) {
      case 'connected':
        return {
          icon: <CheckCircleIcon fontSize="small" />,
          color: 'success',
          label: 'Connected',
        };
      case 'error':
        return {
          icon: <ErrorIcon fontSize="small" />,
          color: 'error',
          label: 'Error',
        };
      case 'unconfigured':
        return {
          icon: <WarningIcon fontSize="small" />,
          color: 'warning',
          label: 'Unconfigured',
        };
      default:
        return {
          icon: <HelpIcon fontSize="small" />,
          color: 'default',
          label: status || 'Unknown',
        };
    }
  };

  return (
    <Card variant="outlined">
      <CardHeader title="Connection Status" />
      <CardContent>
        <Grid container spacing={2}>
          {connections.map((conn) => {
            const config = getStatusConfig(conn.status);

            return (
              <Grid item xs={12} key={conn.service}>
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    p: 2,
                    border: 1,
                    borderColor: 'divider',
                    borderRadius: 1,
                    bgcolor: conn.status === 'error' ? 'error.light' : 'background.paper',
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="subtitle2" sx={{ fontWeight: 600, textTransform: 'uppercase' }}>
                      {conn.service}
                    </Typography>
                  </Box>

                  <Box sx={{ textAlign: 'right' }}>
                    <Chip
                      icon={config.icon}
                      label={config.label}
                      color={config.color}
                      size="small"
                    />
                    {conn.message && (
                      <Typography variant="caption" display="block" color="text.secondary" sx={{ mt: 0.5 }}>
                        {conn.message}
                      </Typography>
                    )}
                  </Box>
                </Box>
              </Grid>
            );
          })}
        </Grid>
      </CardContent>
    </Card>
  );
}
