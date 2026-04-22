import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Collapse,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  Step,
  StepLabel,
  Stepper,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import { api, ORCHESTRATOR_STRATEGIES } from '../api/client.js';

const LAST_REPO_KEY = 'syntexa_last_repo_id';

const TASK_TEMPLATES = [
  {
    label: 'Fix a bug',
    prompt:
      'Fix the following bug: <describe the bug, reproduction steps, and expected behavior>.',
  },
  {
    label: 'Add a feature',
    prompt:
      'Add a new feature: <describe the feature, the user stories, and any acceptance criteria>.',
  },
  {
    label: 'Refactor module',
    prompt:
      'Refactor the following module: <file or package>. Keep behavior identical but improve <readability/performance/structure>.',
  },
];

const STEPS = ['Repository', 'Task', 'Agents'];

function slugify(name) {
  return (name || '')
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9_-]+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '')
    .slice(0, 64);
}

export default function WizardPage() {
  const [activeStep, setActiveStep] = useState(0);

  // Step 1: repository
  const [repositories, setRepositories] = useState([]);
  const [selectedRepoId, setSelectedRepoId] = useState(
    () => Number(localStorage.getItem(LAST_REPO_KEY)) || '',
  );
  const [newRepoOpen, setNewRepoOpen] = useState(false);
  const [newRepo, setNewRepo] = useState({ name: '', path: '' });
  const [repoBusy, setRepoBusy] = useState(false);

  // Step 2: task
  const [taskText, setTaskText] = useState('');

  // Step 3: agents
  const [agents, setAgents] = useState([]);
  const [selectedAgentIds, setSelectedAgentIds] = useState([]);
  const [providers, setProviders] = useState([]);
  const [quickAgentOpen, setQuickAgentOpen] = useState(false);
  const [quickAgent, setQuickAgent] = useState({
    name: '',
    system_prompt: '',
    provider_id: '',
  });
  const [agentBusy, setAgentBusy] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [strategy, setStrategy] = useState('auto');
  const [manualOrder, setManualOrder] = useState([]);

  // Presets (Phase 9)
  const [swarmTemplates, setSwarmTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [seedingAgents, setSeedingAgents] = useState(false);

  // Submission state
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);
  const [runResult, setRunResult] = useState(null);
  const [loadError, setLoadError] = useState(null);

  const loadAll = useCallback(async () => {
    setLoadError(null);
    try {
      const [repoData, agentData, providerData, templates] = await Promise.all([
        api.repositories.list(),
        api.agents.list(),
        api.llmProviders.list(),
        api.presets.swarmTemplates().catch(() => []),
      ]);
      setRepositories(repoData.repositories || []);
      setAgents(agentData.agents || []);
      setProviders(providerData.providers || []);
      setSwarmTemplates(Array.isArray(templates) ? templates : []);
    } catch (err) {
      setLoadError(err.message || 'Failed to load wizard data.');
    }
  }, []);

  useEffect(() => {
    loadAll();
  }, [loadAll]);

  // Keep manualOrder aligned with the agent selection.
  useEffect(() => {
    setManualOrder((prev) => {
      const filtered = prev.filter((id) => selectedAgentIds.includes(id));
      const missing = selectedAgentIds.filter((id) => !filtered.includes(id));
      return [...filtered, ...missing];
    });
  }, [selectedAgentIds]);

  const selectedRepo = useMemo(
    () => repositories.find((r) => r.id === Number(selectedRepoId)) || null,
    [repositories, selectedRepoId],
  );

  const canAdvanceStep = () => {
    if (activeStep === 0) return !!selectedRepo;
    if (activeStep === 1) return taskText.trim().length > 0;
    if (activeStep === 2) return selectedAgentIds.length > 0;
    return false;
  };

  const handleNext = () => setActiveStep((s) => Math.min(s + 1, STEPS.length - 1));
  const handleBack = () => setActiveStep((s) => Math.max(s - 1, 0));

  // --- repository helpers -------------------------------------------------

  async function handleCreateRepo() {
    if (!newRepo.name.trim() || !newRepo.path.trim()) return;
    setRepoBusy(true);
    try {
      const created = await api.repositories.create({
        name: slugify(newRepo.name),
        path: newRepo.path.trim(),
      });
      setRepositories((rs) => [...rs, created]);
      setSelectedRepoId(created.id);
      localStorage.setItem(LAST_REPO_KEY, String(created.id));
      setNewRepo({ name: '', path: '' });
      setNewRepoOpen(false);
    } catch (err) {
      setLoadError(err.message || 'Failed to create repository.');
    } finally {
      setRepoBusy(false);
    }
  }

  function handleSelectRepo(id) {
    setSelectedRepoId(id);
    if (id) localStorage.setItem(LAST_REPO_KEY, String(id));
  }

  // --- template + agent helpers ------------------------------------------

  function applyTemplate(prompt) {
    setTaskText((curr) => (curr ? `${curr}\n\n${prompt}` : prompt));
  }

  function toggleAgent(agentId) {
    setSelectedAgentIds((ids) =>
      ids.includes(agentId) ? ids.filter((i) => i !== agentId) : [...ids, agentId],
    );
  }

  async function handleCreateQuickAgent() {
    if (
      !quickAgent.name.trim() ||
      !quickAgent.system_prompt.trim() ||
      !quickAgent.provider_id
    )
      return;
    setAgentBusy(true);
    try {
      const created = await api.agents.create({
        name: slugify(quickAgent.name),
        system_prompt: quickAgent.system_prompt,
        provider_id: Number(quickAgent.provider_id),
      });
      setAgents((as) => [...as, created]);
      setSelectedAgentIds((ids) => [...ids, created.id]);
      setQuickAgent({ name: '', system_prompt: '', provider_id: '' });
      setQuickAgentOpen(false);
    } catch (err) {
      setLoadError(err.message || 'Failed to create agent.');
    } finally {
      setAgentBusy(false);
    }
  }

  // --- preset helpers ----------------------------------------------------

  function applySwarmTemplate(template) {
    setSelectedTemplate(template.name);
    // Pre-select agents that match preset names; ignore templates that
    // reference agents the user hasn't seeded yet.
    const matchedIds = (template.agent_names || [])
      .map((n) => agents.find((a) => a.name === n)?.id)
      .filter((id) => id != null);
    setSelectedAgentIds(matchedIds);
    setStrategy(template.orchestrator_strategy || 'auto');
  }

  async function handleSeedPresetAgents() {
    const providerId = providers[0]?.id;
    if (!providerId) {
      setLoadError(
        'Add an LLM provider first (Advanced → LLM Providers), then seed presets.',
      );
      return;
    }
    setSeedingAgents(true);
    try {
      const presetAgents = await api.presets.agents();
      const created = [];
      for (const preset of presetAgents) {
        const existing = agents.find((a) => a.name === preset.name);
        if (existing) {
          created.push(existing);
          continue;
        }
        const resp = await api.presets.apply({
          kind: 'agent',
          preset_name: preset.name,
          overrides: { provider_id: providerId },
        });
        if (resp?.agent) created.push(resp.agent);
      }
      // Refresh agent list from server
      const agentData = await api.agents.list();
      setAgents(agentData.agents || []);
    } catch (err) {
      setLoadError(err.message || 'Failed to seed preset agents.');
    } finally {
      setSeedingAgents(false);
    }
  }

  function moveOrder(idx, dir) {
    setManualOrder((order) => {
      const next = [...order];
      const target = idx + dir;
      if (target < 0 || target >= next.length) return order;
      [next[idx], next[target]] = [next[target], next[idx]];
      return next;
    });
  }

  // --- submission ---------------------------------------------------------

  async function handleRun() {
    setSubmitting(true);
    setSubmitError(null);
    setRunResult(null);
    try {
      const payload = {
        name: slugify(`wizard-${Date.now()}`),
        repository_id: Number(selectedRepoId),
        agent_ids: selectedAgentIds,
        task_description: taskText.trim(),
        orchestrator_strategy: strategy,
      };
      if (strategy === 'sequential' && manualOrder.length > 0) {
        payload.manual_agent_order = manualOrder;
      }
      const swarm = await api.swarms.create(payload);
      const result = await api.swarms.run(swarm.id, {});
      setRunResult({ swarm, result });
    } catch (err) {
      setSubmitError(err.message || 'Failed to run swarm.');
    } finally {
      setSubmitting(false);
    }
  }

  // --- rendering ---------------------------------------------------------

  const stepContent = [
    // Step 1: Repository
    <Card key="repo" variant="outlined" sx={{ mt: 3 }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Pick a repository
        </Typography>
        <FormControl fullWidth sx={{ mt: 1 }}>
          <InputLabel id="repo-select-label">Repository</InputLabel>
          <Select
            labelId="repo-select-label"
            label="Repository"
            value={selectedRepoId || ''}
            onChange={(e) => handleSelectRepo(e.target.value)}
          >
            {repositories.length === 0 && (
              <MenuItem value="" disabled>
                No repositories yet — add one below
              </MenuItem>
            )}
            {repositories.map((repo) => (
              <MenuItem key={repo.id} value={repo.id}>
                {repo.name} — {repo.path}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <Box sx={{ mt: 2 }}>
          <Button
            startIcon={<AddIcon />}
            variant="outlined"
            onClick={() => setNewRepoOpen(true)}
          >
            Add new repository
          </Button>
        </Box>
      </CardContent>
    </Card>,

    // Step 2: Task
    <Card key="task" variant="outlined" sx={{ mt: 3 }}>
      <CardContent>
        {swarmTemplates.length > 0 && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle2" gutterBottom>
              Start from a swarm template
            </Typography>
            <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', gap: 1 }}>
              {swarmTemplates.map((tpl) => (
                <Chip
                  key={tpl.name}
                  label={tpl.name}
                  title={tpl.description}
                  onClick={() => applySwarmTemplate(tpl)}
                  color={selectedTemplate === tpl.name ? 'primary' : 'default'}
                  variant={selectedTemplate === tpl.name ? 'filled' : 'outlined'}
                  clickable
                />
              ))}
            </Stack>
            <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
              Templates pre-select agents and strategy for Step 3.
            </Typography>
          </Box>
        )}
        <Typography variant="h6" gutterBottom>
          What do you want to build?
        </Typography>
        <TextField
          fullWidth
          multiline
          minRows={6}
          size="medium"
          placeholder="Describe the task in plain English…"
          value={taskText}
          onChange={(e) => setTaskText(e.target.value)}
        />
        <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
          Templates
        </Typography>
        <Stack direction="row" spacing={1} sx={{ mt: 1, flexWrap: 'wrap', gap: 1 }}>
          {TASK_TEMPLATES.map((t) => (
            <Chip
              key={t.label}
              label={t.label}
              onClick={() => applyTemplate(t.prompt)}
              variant="outlined"
              clickable
            />
          ))}
        </Stack>
      </CardContent>
    </Card>,

    // Step 3: Agents
    <Card key="agents" variant="outlined" sx={{ mt: 3 }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Pick agents
        </Typography>
        {agents.length === 0 && (
          <Alert severity="info" sx={{ mb: 2 }}>
            No agents yet. Seed the built-in presets or create one below.
          </Alert>
        )}
        {agents.length === 0 && (
          <Box sx={{ mb: 2 }}>
            <Button
              variant="contained"
              onClick={handleSeedPresetAgents}
              disabled={seedingAgents || providers.length === 0}
              startIcon={
                seedingAgents ? (
                  <CircularProgress size={14} color="inherit" />
                ) : (
                  <AddIcon />
                )
              }
            >
              {seedingAgents ? 'Seeding…' : 'Seed preset agents'}
            </Button>
            {providers.length === 0 && (
              <Typography variant="caption" color="text.secondary" sx={{ ml: 2 }}>
                Add an LLM provider first.
              </Typography>
            )}
          </Box>
        )}
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
          {agents.map((agent) => {
            const selected = selectedAgentIds.includes(agent.id);
            return (
              <Chip
                key={agent.id}
                label={agent.name}
                onClick={() => toggleAgent(agent.id)}
                color={selected ? 'primary' : 'default'}
                variant={selected ? 'filled' : 'outlined'}
                clickable
              />
            );
          })}
        </Box>
        <Box sx={{ mt: 2 }}>
          <Button
            startIcon={<AddIcon />}
            variant="outlined"
            onClick={() => setQuickAgentOpen(true)}
          >
            Create quick agent
          </Button>
        </Box>

        <Divider sx={{ my: 3 }} />

        <Button
          size="small"
          onClick={() => setShowAdvanced((s) => !s)}
          endIcon={showAdvanced ? <ExpandLessIcon /> : <ExpandMoreIcon />}
        >
          Advanced
        </Button>
        <Collapse in={showAdvanced}>
          <Box sx={{ mt: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Orchestrator strategy
            </Typography>
            <ToggleButtonGroup
              value={strategy}
              exclusive
              onChange={(_, v) => v && setStrategy(v)}
              size="small"
            >
              {ORCHESTRATOR_STRATEGIES.map((s) => (
                <ToggleButton key={s} value={s} sx={{ textTransform: 'capitalize' }}>
                  {s}
                </ToggleButton>
              ))}
            </ToggleButtonGroup>

            {strategy === 'sequential' && manualOrder.length > 0 && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Manual agent order
                </Typography>
                <Stack spacing={1}>
                  {manualOrder.map((agentId, idx) => {
                    const agent = agents.find((a) => a.id === agentId);
                    return (
                      <Box
                        key={agentId}
                        sx={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: 1,
                          p: 1,
                          border: 1,
                          borderColor: 'divider',
                          borderRadius: 1,
                        }}
                      >
                        <Typography sx={{ flex: 1 }}>
                          {idx + 1}. {agent?.name || `Agent ${agentId}`}
                        </Typography>
                        <Button
                          size="small"
                          disabled={idx === 0}
                          onClick={() => moveOrder(idx, -1)}
                        >
                          Up
                        </Button>
                        <Button
                          size="small"
                          disabled={idx === manualOrder.length - 1}
                          onClick={() => moveOrder(idx, 1)}
                        >
                          Down
                        </Button>
                      </Box>
                    );
                  })}
                </Stack>
              </Box>
            )}
          </Box>
        </Collapse>
      </CardContent>
    </Card>,
  ];

  return (
    <Box sx={{ width: '100%', maxWidth: 900, mx: 'auto' }}>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" component="h1" sx={{ fontWeight: 600 }}>
          New Swarm
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Three steps: pick a repo, describe the task, pick your agents.
        </Typography>
      </Box>

      {loadError && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setLoadError(null)}>
          {loadError}
        </Alert>
      )}

      <Stepper activeStep={activeStep} sx={{ mb: 2 }}>
        {STEPS.map((label) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>

      {stepContent[activeStep]}

      <Box sx={{ mt: 3, display: 'flex', justifyContent: 'space-between' }}>
        <Button onClick={handleBack} disabled={activeStep === 0 || submitting}>
          Back
        </Button>
        {activeStep < STEPS.length - 1 ? (
          <Button
            variant="contained"
            onClick={handleNext}
            disabled={!canAdvanceStep()}
          >
            Next
          </Button>
        ) : (
          <Button
            variant="contained"
            startIcon={submitting ? <CircularProgress size={16} color="inherit" /> : <PlayArrowIcon />}
            disabled={!canAdvanceStep() || submitting}
            onClick={handleRun}
          >
            {submitting ? 'Running…' : 'Create & Run Swarm'}
          </Button>
        )}
      </Box>

      {submitError && (
        <Alert severity="error" sx={{ mt: 3 }} onClose={() => setSubmitError(null)}>
          {submitError}
        </Alert>
      )}

      {runResult && <RunResultCard data={runResult} agents={agents} />}

      {/* Add repo dialog */}
      <Dialog open={newRepoOpen} onClose={() => setNewRepoOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>Add repository</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField
              label="Name"
              value={newRepo.name}
              onChange={(e) => setNewRepo((r) => ({ ...r, name: e.target.value }))}
              helperText="Short slug (letters, numbers, dashes)."
              autoFocus
            />
            <TextField
              label="Absolute path"
              value={newRepo.path}
              onChange={(e) => setNewRepo((r) => ({ ...r, path: e.target.value }))}
              placeholder="/home/you/code/my-project"
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setNewRepoOpen(false)} disabled={repoBusy}>
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={handleCreateRepo}
            disabled={repoBusy || !newRepo.name.trim() || !newRepo.path.trim()}
          >
            {repoBusy ? 'Creating…' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Quick agent dialog */}
      <Dialog
        open={quickAgentOpen}
        onClose={() => setQuickAgentOpen(false)}
        fullWidth
        maxWidth="sm"
      >
        <DialogTitle>Create quick agent</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField
              label="Name"
              value={quickAgent.name}
              onChange={(e) => setQuickAgent((a) => ({ ...a, name: e.target.value }))}
              autoFocus
            />
            <TextField
              label="System prompt"
              multiline
              minRows={4}
              value={quickAgent.system_prompt}
              onChange={(e) =>
                setQuickAgent((a) => ({ ...a, system_prompt: e.target.value }))
              }
            />
            <FormControl fullWidth>
              <InputLabel id="provider-select-label">LLM provider</InputLabel>
              <Select
                labelId="provider-select-label"
                label="LLM provider"
                value={quickAgent.provider_id}
                onChange={(e) =>
                  setQuickAgent((a) => ({ ...a, provider_id: e.target.value }))
                }
              >
                {providers.length === 0 && (
                  <MenuItem value="" disabled>
                    No providers — add one in Advanced → LLM Providers
                  </MenuItem>
                )}
                {providers.map((p) => (
                  <MenuItem key={p.id} value={p.id}>
                    {p.name} ({p.provider_type} — {p.default_model})
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setQuickAgentOpen(false)} disabled={agentBusy}>
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={handleCreateQuickAgent}
            disabled={
              agentBusy ||
              !quickAgent.name.trim() ||
              !quickAgent.system_prompt.trim() ||
              !quickAgent.provider_id
            }
          >
            {agentBusy ? 'Creating…' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

function RunResultCard({ data, agents }) {
  const { swarm, result } = data;
  return (
    <Card variant="outlined" sx={{ mt: 3 }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Swarm "{swarm.name}" — {result.success ? 'success' : 'failed'}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Strategy: {result.strategy_used}
          {result.order && ` — order: ${result.order.join(' → ')}`}
        </Typography>
        {result.error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {result.error}
          </Alert>
        )}
        <Divider sx={{ mb: 2 }} />
        <Typography variant="subtitle2" gutterBottom>
          Agent outputs
        </Typography>
        <Stack spacing={2}>
          {Object.entries(result.agent_outputs || {}).map(([agentId, output]) => {
            const agent = agents.find((a) => String(a.id) === String(agentId));
            return (
              <Box
                key={agentId}
                sx={{
                  p: 2,
                  borderRadius: 1,
                  border: 1,
                  borderColor: 'divider',
                  bgcolor: 'background.default',
                }}
              >
                <Typography variant="subtitle2" sx={{ mb: 1 }}>
                  {agent?.name || `Agent ${agentId}`}
                </Typography>
                <Typography
                  variant="body2"
                  component="pre"
                  sx={{
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                    fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace',
                    fontSize: '0.8rem',
                    m: 0,
                  }}
                >
                  {output}
                </Typography>
              </Box>
            );
          })}
        </Stack>
      </CardContent>
    </Card>
  );
}
