import React, { memo, useMemo } from 'react';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Chip,
  IconButton,
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
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import CodeIcon from '@mui/icons-material/Code';

// Memoized row component - prevents re-renders when parent updates
const SwarmRow = memo(function SwarmRow({ swarm }) {
  const duration = useMemo(() => {
    const start = new Date(swarm.started_at);
    const now = new Date();
    const diffMs = now - start;
    const diffMins = Math.floor(diffMs / 60000);
    const hours = Math.floor(diffMins / 60);
    const mins = diffMins % 60;

    if (hours > 0) {
      return `${hours}h ${mins}m`;
    }
    return `${mins}m`;
  }, [swarm.started_at]);

  return (
    <TableRow hover>
      <TableCell>
        <Box>
          <Typography variant="body2" fontWeight={500}>
            {swarm.task_name}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {swarm.task_id}
          </Typography>
        </Box>
      </TableCell>
      <TableCell>
        <Chip
          label={swarm.task_type}
          size="small"
          color="primary"
          sx={{ textTransform: 'capitalize' }}
        />
      </TableCell>
      <TableCell>
        <Typography variant="body2">
          {swarm.active_agent || '—'}
        </Typography>
      </TableCell>
      <TableCell>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <CodeIcon fontSize="small" color="action" />
          <Typography variant="body2" component="code" sx={{ fontSize: '0.75rem' }}>
            {swarm.branch}
          </Typography>
        </Box>
      </TableCell>
      <TableCell>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <AccessTimeIcon fontSize="small" color="action" />
          <Typography variant="body2" color="text.secondary">
            {duration}
          </Typography>
        </Box>
      </TableCell>
    </TableRow>
  );
});

/**
 * ActiveSwarms - MUI Card with table for active swarms
 *
 * Uses memoized components for performance optimization (Vercel best practice).
 */
export default function ActiveSwarms({ swarms, loading, onRefresh }) {
  // Early return for loading state - before any expensive computation
  if (loading) {
    return (
      <Card variant="outlined" sx={{ mb: 3 }}>
        <CardHeader title="Active Swarms" />
        <CardContent>
          <Skeleton variant="rectangular" height={200} />
        </CardContent>
      </Card>
    );
  }

  // Early return for empty state
  if (!swarms || swarms.length === 0) {
    return (
      <Card variant="outlined" sx={{ mb: 3 }}>
        <CardHeader
          title="Active Swarms"
          action={
            <Tooltip title="Refresh">
              <IconButton onClick={onRefresh} size="small">
                <RefreshIcon />
              </IconButton>
            </Tooltip>
          }
        />
        <CardContent>
          <Box sx={{ textAlign: 'center', py: 4, color: 'text.secondary' }}>
            <Typography variant="body1" gutterBottom>
              No active swarms.
            </Typography>
            <Typography variant="body2">
              Tag a task in ClickUp to start a swarm.
            </Typography>
          </Box>
        </CardContent>
      </Card>
    );
  }

  // Main render with data
  return (
    <Card variant="outlined" sx={{ mb: 3 }}>
      <CardHeader
        title={`Active Swarms (${swarms.length})`}
        action={
          <Tooltip title="Refresh">
            <IconButton onClick={onRefresh} disabled={loading} size="small">
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        }
      />
      <CardContent sx={{ p: 0 }}>
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Task</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Active Agent</TableCell>
                <TableCell>Branch</TableCell>
                <TableCell>Duration</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {swarms.map((swarm) => (
                <SwarmRow key={swarm.id} swarm={swarm} />
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </CardContent>
    </Card>
  );
}
