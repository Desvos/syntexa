import React, { memo } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  CardHeader,
  Chip,
  IconButton,
  Link,
  Skeleton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tooltip,
  Typography,
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import TimerOffIcon from '@mui/icons-material/TimerOff';
import VisibilityIcon from '@mui/icons-material/Visibility';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';

// Status configurations
const STATUS_CONFIG = {
  completed: { icon: CheckCircleIcon, color: 'success', label: 'Completed' },
  failed: { icon: ErrorIcon, color: 'error', label: 'Failed' },
  timeout: { icon: TimerOffIcon, color: 'warning', label: 'Timeout' },
};

const getStatusConfig = (status) => {
  return STATUS_CONFIG[status] || { icon: ErrorIcon, color: 'default', label: status };
};

// Memoized row component
const SwarmRow = memo(function SwarmRow({ swarm, onViewLog, selectedSwarmId }) {
  const statusConfig = getStatusConfig(swarm.status);
  const StatusIcon = statusConfig.icon;

  const formatDuration = () => {
    if (!swarm.completed_at) return '—';
    const start = new Date(swarm.started_at);
    const end = new Date(swarm.completed_at);
    const diffMs = end - start;
    const diffMins = Math.floor(diffMs / 60000);
    const hours = Math.floor(diffMins / 60);
    const mins = diffMins % 60;
    const secs = Math.floor((diffMs % 60000) / 1000);

    if (hours > 0) {
      return `${hours}h ${mins}m ${secs}s`;
    }
    return `${mins}m ${secs}s`;
  };

  const formatDate = (dateString) => {
    if (!dateString) return '—';
    return new Date(dateString).toLocaleString();
  };

  const isSelected = selectedSwarmId === swarm.id;

  return (
    <TableRow
      hover
      selected={isSelected}
      sx={{ '&.Mui-selected': { backgroundColor: 'action.selected' } }}
    >
      <TableCell>
        <Chip
          icon={<StatusIcon fontSize="small" />}
          label={statusConfig.label}
          size="small"
          color={statusConfig.color}
        />
      </TableCell>
      <TableCell>
        <Box>
          <Typography variant="body2" fontWeight={500}>
            {swarm.task_name}
          </Typography>
          {swarm.pr_url && (
            <Link
              href={swarm.pr_url}
              target="_blank"
              rel="noopener noreferrer"
              sx={{ display: 'flex', alignItems: 'center', gap: 0.5, fontSize: '0.75rem' }}
            >
              View PR <OpenInNewIcon fontSize="inherit" />
            </Link>
          )}
        </Box>
      </TableCell>
      <TableCell>
        <Chip
          label={swarm.task_type}
          size="small"
          variant="outlined"
          sx={{ textTransform: 'capitalize' }}
        />
      </TableCell>
      <TableCell>
        <Typography variant="body2" color="text.secondary">
          {formatDuration()}
        </Typography>
      </TableCell>
      <TableCell>
        <Typography variant="body2" color="text.secondary">
          {formatDate(swarm.completed_at)}
        </Typography>
      </TableCell>
      <TableCell>
        <Button
          size="small"
          startIcon={isSelected ? undefined : <VisibilityIcon fontSize="small" />}
          onClick={() => onViewLog(swarm.id)}
          disabled={isSelected}
          variant={isSelected ? 'outlined' : 'text'}
        >
          {isSelected ? 'Viewing...' : 'View Log'}
        </Button>
      </TableCell>
    </TableRow>
  );
});

/**
 * CompletedSwarms - MUI Card with table for completed swarms
 */
export default function CompletedSwarms({ swarms, loading, onViewLog, selectedSwarmId }) {
  // Early return for loading
  if (loading) {
    return (
      <Card variant="outlined">
        <CardHeader title="Completed Swarms" />
        <CardContent>
          <Skeleton variant="rectangular" height={300} />
        </CardContent>
      </Card>
    );
  }

  // Early return for empty
  if (!swarms || swarms.length === 0) {
    return (
      <Card variant="outlined">
        <CardHeader title="Completed Swarms" />
        <CardContent>
          <Box sx={{ textAlign: 'center', py: 4, color: 'text.secondary' }}>
            <Typography>No completed swarms yet.</Typography>
          </Box>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card variant="outlined">
      <CardHeader title={`Completed Swarms (${swarms.length} shown)`} />
      <CardContent sx={{ p: 0 }}>
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Status</TableCell>
                <TableCell>Task</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Duration</TableCell>
                <TableCell>Completed</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {swarms.map((swarm) => (
                <SwarmRow
                  key={swarm.id}
                  swarm={swarm}
                  onViewLog={onViewLog}
                  selectedSwarmId={selectedSwarmId}
                />
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </CardContent>
    </Card>
  );
}
