import React, { memo } from 'react';
import {
  Box,
  Chip,
  CircularProgress,
  Dialog,
  DialogContent,
  DialogTitle,
  Divider,
  IconButton,
  Link,
  Paper,
  Typography,
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import TimerOffIcon from '@mui/icons-material/TimerOff';
import HelpIcon from '@mui/icons-material/Help';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';

const STATUS_CONFIG = {
  completed: { icon: CheckCircleIcon, color: 'success', label: 'Completed' },
  failed: { icon: ErrorIcon, color: 'error', label: 'Failed' },
  timeout: { icon: TimerOffIcon, color: 'warning', label: 'Timeout' },
  running: { icon: CircularProgress, color: 'info', label: 'Running' },
};

const getStatusConfig = (status) => {
  return STATUS_CONFIG[status] || { icon: HelpIcon, color: 'default', label: status };
};

// Memoized metadata item
const MetaItem = memo(function MetaItem({ label, value, isLink }) {
  return (
    <Box sx={{ mb: 1 }}>
      <Typography variant="caption" color="text.secondary" component="dt" sx={{ fontWeight: 600 }}>
        {label}:
      </Typography>
      <Typography variant="body2" component="dd">
        {isLink ? (
          <Link href={value} target="_blank" rel="noopener noreferrer" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            {value} <OpenInNewIcon fontSize="inherit" />
          </Link>
        ) : (
          value
        )}
      </Typography>
    </Box>
  );
});

/**
 * LogViewer - MUI Dialog for viewing swarm logs
 *
 * Features:
 * - Full-screen dialog with scrollable content
 * - Status chip with colored icon
 * - Metadata display with definition list
 * - Preformatted log content
 */
export default function LogViewer({ logData, loading, onClose }) {
  const open = Boolean(logData) || loading;

  if (!open) return null;

  const statusConfig = logData ? getStatusConfig(logData.status) : null;
  const StatusIcon = statusConfig?.icon;

  const formatDate = (dateString) => {
    if (!dateString) return '—';
    return new Date(dateString).toLocaleString();
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="lg"
      fullWidth
      scroll="paper"
      aria-labelledby="log-viewer-title"
    >
      <DialogTitle
        id="log-viewer-title"
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 2,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {loading ? (
            <>
              <CircularProgress size={20} />
              <Typography variant="h6">Loading log...</Typography>
            </>
          ) : (
            <>
              {StatusIcon && <StatusIcon color={statusConfig.color} fontSize="small" />}
              <Typography variant="h6">{logData.task_name}</Typography>
              <Chip
                label={statusConfig?.label || logData.status}
                color={statusConfig?.color || 'default'}
                size="small"
              />
            </>
          )}
        </Box>

        <IconButton onClick={onClose} size="small" edge="end" aria-label="close">
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent dividers>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <>
            {/* Metadata Section */}
            <Paper variant="outlined" sx={{ p: 2, mb: 3 }}>
              <Typography variant="subtitle2" gutterBottom>
                Swarm Details
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <Box component="dl" sx={{ m: 0 }}>
                <MetaItem label="Task ID" value={logData.task_id} />
                <MetaItem label="Status" value={logData.status} />
                <MetaItem label="Started" value={formatDate(logData.started_at)} />
                {logData.completed_at && (
                  <MetaItem label="Completed" value={formatDate(logData.completed_at)} />
                )}
                {logData.pr_url && (
                  <MetaItem label="PR URL" value={logData.pr_url} isLink />
                )}
              </Box>
            </Paper>

            {/* Log Content */}
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Conversation Log
              </Typography>
              <Paper
                variant="outlined"
                sx={{
                  p: 2,
                  backgroundColor: 'grey.50',
                  maxHeight: '500px',
                  overflow: 'auto',
                }}
              >
                {logData.log ? (
                  <Box
                    component="pre"
                    sx={{
                      m: 0,
                      fontFamily: 'monospace',
                      fontSize: '0.875rem',
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word',
                    }}
                  >
                    {logData.log}
                  </Box>
                ) : (
                  <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                    No conversation log available.
                    {logData.status === 'running' && ' Swarm is still active.'}
                    {(logData.status === 'completed' || logData.status === 'failed') &&
                      ' Log may have been cleaned up due to retention policy.'}
                  </Typography>
                )}
              </Paper>
            </Box>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
