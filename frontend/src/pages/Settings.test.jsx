/** T071 — component tests for the Settings page. */
import React from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import SettingsPage from './Settings.jsx';

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
      settings: {
        get: vi.fn(),
        update: vi.fn(),
        status: vi.fn(),
      },
    },
  };
});

import { api } from '../api/client.js';

const DEFAULT_SETTINGS = {
  poll_interval: 300,
  max_concurrent: 3,
  log_retention_days: 30,
  agent_trigger_tag: 'agent-swarm',
  base_branch: 'main',
  repo_path: '.',
};

const DEFAULT_CONNECTIONS = [
  {
    service: 'clickup',
    status: 'connected',
    message: 'ClickUp API key and list ID configured',
  },
  {
    service: 'github',
    status: 'connected',
    message: 'GitHub token, owner and repo configured',
  },
];

beforeEach(() => {
  vi.clearAllMocks();
  api.settings.get.mockResolvedValue(DEFAULT_SETTINGS);
  api.settings.status.mockResolvedValue({ connections: DEFAULT_CONNECTIONS });
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe('SettingsPage', () => {
  it('loads and displays settings', async () => {
    render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByDisplayValue('300')).toBeInTheDocument();
    });

    expect(screen.getByDisplayValue('3')).toBeInTheDocument();
    expect(screen.getByDisplayValue('agent-swarm')).toBeInTheDocument();
    expect(screen.getByDisplayValue('main')).toBeInTheDocument();
  });

  it('displays connection status', async () => {
    render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByText('CLICKUP')).toBeInTheDocument();
    });

    expect(screen.getByText('GITHUB')).toBeInTheDocument();
    expect(screen.getAllByText('connected').length).toBeGreaterThanOrEqual(2);
  });

  it('updates settings when save is clicked', async () => {
    const user = userEvent.setup();
    api.settings.update.mockResolvedValue({
      ...DEFAULT_SETTINGS,
      poll_interval: 120,
    });

    render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByDisplayValue('300')).toBeInTheDocument();
    });

    const pollInput = screen.getByLabelText(/Poll Interval/i);
    await user.clear(pollInput);
    await user.type(pollInput, '120');

    await user.click(screen.getByRole('button', { name: /Save Changes/i }));

    await waitFor(() => {
      expect(api.settings.update).toHaveBeenCalledWith({ poll_interval: 120 });
    });

    expect(await screen.findByText(/saved successfully/i)).toBeInTheDocument();
  });

  it('disables save button when no changes are made', async () => {
    render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Save Changes/i })).toBeDisabled();
    });
  });

  it('shows error when API fails', async () => {
    const user = userEvent.setup();
    api.settings.update.mockRejectedValue({
      message: 'Update failed',
    });

    render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByDisplayValue('300')).toBeInTheDocument();
    });

    const pollInput = screen.getByLabelText(/Poll Interval/i);
    await user.clear(pollInput);
    await user.type(pollInput, '120');

    await user.click(screen.getByRole('button', { name: /Save Changes/i }));

    expect(await screen.findByRole('alert')).toBeInTheDocument();
  });
});
