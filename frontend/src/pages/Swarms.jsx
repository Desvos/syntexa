import React, { useCallback, useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Dialog,
  DialogContent,
  DialogTitle,
  Divider,
  IconButton,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Toolbar,
  Tooltip,
  Typography,
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import DeleteIcon from '@mui/icons-material/Delete';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import VisibilityIcon from '@mui/icons-material/Visibility';
import { api } from '../api/client.js';

const STATUS_COLORS = {
  idle: 'default',
  running: 'info',
  completed: 'success',
  failed: 'error',
};

export default function SwarmsPage() {
  const [swarms, setSwarms] = useState([]);
  const [repos, setRepos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [runningId, setRunningId] = useState(null);
  const [lastResults, setLastResults] = useState({}); // id -> result
  const [detailOpen, setDetailOpen] = useState(false);
  const [detailSwarm, setDetailSwarm] = useState(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [swarmData, repoData] = await Promise.all([
        api.swarms.list(),
        api.repositories.list(),
      ]);
      setSwarms(swarmData.swarms || []);
      setRepos(repoData.repositories || []);
    } catch (err) {
      setError(err.message || 'Failed to load swarms.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function handleRun(swarm) {
    setRunningId(swarm.id);
    setError(null);
    try {
      const result = await api.swarms.run(swarm.id, {});
      setLastResults((m) => ({ ...m, [swarm.id]: result }));
      await refresh();
    } catch (err) {
      setError(err.message || 'Run failed.');
    } finally {
      setRunningId(null);
    }
  }

  async function handleDelete(swarm) {
    if (!window.confirm(`Delete swarm "${swarm.name}"?`)) return;
    try {
      await api.swarms.remove(swarm.id);
      await refresh();
    } catch (err) {
      setError(err.message || 'Delete failed.');
    }
  }

  function openDetail(swarm) {
    setDetailSwarm(swarm);
    setDetailOpen(true);
  }

  function repoName(id) {
    const r = repos.find((rr) => rr.id === id);
    return r ? r.name : `#${id}`;
  }

  return (
    <Box>
      <Box sx={{ mb: 2 }}>
        <Typography variant="h4" component="h1" sx={{ fontWeight: 600 }}>
          Swarms
        </Typography>
        <Typography variant="body2" color="text.secondary">
          A swarm is one running swarm-job instance attached to a repository, scoped to a task.
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Toolbar sx={{ justifyContent: 'space-between', px: 0, mb: 2 }}>
        <Typography variant="h6">All swarms</Typography>
        <Tooltip title="Refresh">
          <IconButton onClick={refresh} disabled={loading}>
            <RefreshIcon />
          </IconButton>
        </Tooltip>
      </Toolbar>

      <Card variant="outlined">
        <CardContent sx={{ p: 0 }}>
          {loading ? (
            <Box sx={{ p: 4, textAlign: 'center' }}>
              <CircularProgress size={24} />
            </Box>
          ) : swarms.length === 0 ? (
            <Box sx={{ p: 3, textAlign: 'center' }}>
              <Typography color="text.secondary">
                No swarms yet. Create one via the wizard.
              </Typography>
            </Box>
          ) : (
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell>Repository</TableCell>
                  <TableCell>Strategy</TableCell>
                  <TableCell>Agents</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {swarms.map((s) => (
                  <React.Fragment key={s.id}>
                    <TableRow hover>
                      <TableCell>{s.name}</TableCell>
                      <TableCell>{repoName(s.repository_id)}</TableCell>
                      <TableCell>
                        <Chip label={s.orchestrator_strategy} size="small" />
                      </TableCell>
                      <TableCell>{(s.agents || []).length}</TableCell>
                      <TableCell>
                        <Chip
                          label={s.status}
                          size="small"
                          color={STATUS_COLORS[s.status] || 'default'}
                        />
                      </TableCell>
                      <TableCell align="right">
                        <Tooltip title="Details">
                          <IconButton size="small" onClick={() => openDetail(s)}>
                            <VisibilityIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Run swarm">
                          <span>
                            <IconButton
                              size="small"
                              color="primary"
                              onClick={() => handleRun(s)}
                              disabled={runningId === s.id || s.status === 'running'}
                            >
                              {runningId === s.id ? (
                                <CircularProgress size={18} />
                              ) : (
                                <PlayArrowIcon fontSize="small" />
                              )}
                            </IconButton>
                          </span>
                        </Tooltip>
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => handleDelete(s)}
                          aria-label="delete"
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                    {lastResults[s.id] && (
                      <TableRow>
                        <TableCell colSpan={6} sx={{ bgcolor: 'background.default' }}>
                          <RunResultInline result={lastResults[s.id]} agents={s.agents} />
                        </TableCell>
                      </TableRow>
                    )}
                  </React.Fragment>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Dialog
        open={detailOpen}
        onClose={() => setDetailOpen(false)}
        fullWidth
        maxWidth="md"
      >
        <DialogTitle>Swarm: {detailSwarm?.name}</DialogTitle>
        <DialogContent>
          {detailSwarm && (
            <Stack spacing={2}>
              <Box>
                <Typography variant="subtitle2">Repository</Typography>
                <Typography variant="body2">{repoName(detailSwarm.repository_id)}</Typography>
              </Box>
              <Box>
                <Typography variant="subtitle2">Strategy</Typography>
                <Typography variant="body2">{detailSwarm.orchestrator_strategy}</Typography>
              </Box>
              <Box>
                <Typography variant="subtitle2">Task</Typography>
                <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                  {detailSwarm.task_description || '—'}
                </Typography>
              </Box>
              <Box>
                <Typography variant="subtitle2">Agents</Typography>
                <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', gap: 1 }}>
                  {(detailSwarm.agents || []).map((a) => (
                    <Chip key={a.id} label={a.name} size="small" />
                  ))}
                </Stack>
              </Box>
              <Divider />
              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  Last run output
                </Typography>
                {lastResults[detailSwarm.id] ? (
                  <RunResultInline
                    result={lastResults[detailSwarm.id]}
                    agents={detailSwarm.agents}
                  />
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    No run yet this session.
                  </Typography>
                )}
              </Box>
            </Stack>
          )}
        </DialogContent>
      </Dialog>
    </Box>
  );
}

function RunResultInline({ result, agents }) {
  return (
    <Box sx={{ py: 1 }}>
      <Typography variant="caption" color="text.secondary">
        Strategy used: {result.strategy_used}
        {result.order && ` — order: ${result.order.join(' → ')}`} —{' '}
        {result.success ? 'success' : 'failed'}
      </Typography>
      {result.error && (
        <Alert severity="error" sx={{ mt: 1 }}>
          {result.error}
        </Alert>
      )}
      <Stack spacing={1} sx={{ mt: 1 }}>
        {Object.entries(result.agent_outputs || {}).map(([agentId, output]) => {
          const agent = (agents || []).find((a) => String(a.id) === String(agentId));
          return (
            <Box
              key={agentId}
              sx={{
                p: 1.5,
                borderRadius: 1,
                border: 1,
                borderColor: 'divider',
                bgcolor: 'background.paper',
              }}
            >
              <Typography variant="caption" sx={{ fontWeight: 600 }}>
                {agent?.name || `Agent ${agentId}`}
              </Typography>
              <Typography
                component="pre"
                sx={{
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                  fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace',
                  fontSize: '0.75rem',
                  m: 0,
                  mt: 0.5,
                }}
              >
                {output}
              </Typography>
            </Box>
          );
        })}
      </Stack>
    </Box>
  );
}
