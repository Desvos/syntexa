/** T071 — component tests for the Monitor page. */
import React from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import MonitorPage from './Monitor.jsx';

// Mock the api client
vi.mock('../api/client.js', () => {
  return {
    ApiError: class ApiError extends Error {
      constructor(msg, status) {
        super(msg);
        this.status = status;
      }
    },
    api: {
      swarms: {
        active: vi.fn(),
        completed: vi.fn(),
        log: vi.fn(),
      },
    },
  };
});

import { api } from '../api/client.js';

const ACTIVE_SWARMS = [
  {
    id: 1,
    task_id: 'task-123',
    task_name: 'Implement feature X',
    task_type: 'feature',
    branch: 'feature/task-123',
    status: 'running',
    active_agent: 'coder',
    started_at: '2026-04-14T10:00:00Z',
    completed_at: null,
    pr_url: null,
  },
];

const COMPLETED_SWARMS = [
  {
    id: 2,
    task_id: 'task-456',
    task_name: 'Fix bug Y',
    task_type: 'fix',
    branch: 'fix/task-456',
    status: 'completed',
    active_agent: null,
    started_at: '2026-04-14T09:00:00Z',
    completed_at: '2026-04-14T09:15:00Z',
    pr_url: 'https://github.com/org/repo/pull/42',
  },
];

const SWARM_LOG = {
  task_id: 'task-456',
  task_name: 'Fix bug Y',
  status: 'completed',
  log: 'Agent 1: Started working on task\nAgent 2: Reviewed and approved',
  pr_url: 'https://github.com/org/repo/pull/42',
  started_at: '2026-04-14T09:00:00Z',
  completed_at: '2026-04-14T09:15:00Z',
};

beforeEach(() => {
  vi.clearAllMocks();
  api.swarms.active.mockResolvedValue({ swarms: ACTIVE_SWARMS });
  api.swarms.completed.mockResolvedValue({ swarms: COMPLETED_SWARMS });
  api.swarms.log.mockResolvedValue(SWARM_LOG);
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe('MonitorPage', () => {
  it('loads and displays active swarms', async () => {
    render(<MonitorPage />);

    await waitFor(() => {
      expect(screen.getByText('Implement feature X')).toBeInTheDocument();
    });

    expect(screen.getByText('task-123')).toBeInTheDocument();
    expect(screen.getByText('coder')).toBeInTheDocument();
  });

  it('loads and displays completed swarms', async () => {
    render(<MonitorPage />);

    await waitFor(() => {
      expect(screen.getByText('Fix bug Y')).toBeInTheDocument();
    });

    expect(screen.getByText(/View PR/)).toBeInTheDocument();
  });

  it('shows log viewer when View Log is clicked', async () => {
    const user = userEvent.setup();
    render(<MonitorPage />);

    await waitFor(() => {
      expect(screen.getByText('Fix bug Y')).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: /View Log/i }));

    await waitFor(() => {
      expect(screen.getByText(/Conversation Log/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/Agent 1: Started working on task/i)).toBeInTheDocument();
  });

  it('closes log viewer when close button is clicked', async () => {
    const user = userEvent.setup();
    render(<MonitorPage />);

    await waitFor(() => {
      expect(screen.getByText('Fix bug Y')).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: /View Log/i }));

    await waitFor(() => {
      expect(screen.getByText(/Conversation Log/i)).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: /✕/i }));

    await waitFor(() => {
      expect(screen.queryByText(/Conversation Log/i)).not.toBeInTheDocument();
    });
  });

  it('shows empty state when no active swarms', async () => {
    api.swarms.active.mockResolvedValue({ swarms: [] });

    render(<MonitorPage />);

    await waitFor(() => {
      expect(screen.getByText(/No active swarms/i)).toBeInTheDocument();
    });
  });

  it('refreshes when refresh button is clicked', async () => {
    const user = userEvent.setup();
    render(<MonitorPage />);

    await waitFor(() => {
      expect(screen.getByText('Implement feature X')).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: /Refresh All/i }));

    await waitFor(() => {
      expect(api.swarms.active).toHaveBeenCalledTimes(2);
      expect(api.swarms.completed).toHaveBeenCalledTimes(2);
    });
  });
});
