/** T044 — component tests for the Roles page. */
import React from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import RolesPage from './Roles.jsx';

// Mock the api client so tests don't hit the network.
vi.mock('../api/client.js', () => {
  return {
    ApiError: class ApiError extends Error {
      constructor(msg, status) { super(msg); this.status = status; }
    },
    api: {
      roles: {
        list: vi.fn(),
        create: vi.fn(),
        update: vi.fn(),
        remove: vi.fn(),
      },
    },
  };
});

import { api, ApiError } from '../api/client.js';

const SEED = [
  {
    id: 1,
    name: 'planner',
    system_prompt: 'plan it',
    handoff_targets: ['coder'],
    is_default: true,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  },
  {
    id: 2,
    name: 'custom-auditor',
    system_prompt: 'audit it',
    handoff_targets: ['coder', 'reviewer'],
    is_default: false,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  },
];

beforeEach(() => {
  vi.clearAllMocks();
  api.roles.list.mockResolvedValue({ roles: SEED });
});

afterEach(() => { vi.restoreAllMocks(); });

describe('RolesPage', () => {
  it('lists roles from the API', async () => {
    render(<RolesPage />);

    expect(await screen.findByText('planner')).toBeInTheDocument();
    expect(screen.getByText('custom-auditor')).toBeInTheDocument();
    // Default badge shown on the default role only.
    const plannerRow = screen.getByTestId('role-row-planner');
    expect(plannerRow).toHaveTextContent('default');
  });

  it('blocks deletion of default roles via disabled button', async () => {
    render(<RolesPage />);
    await screen.findByText('planner');

    const plannerRow = screen.getByTestId('role-row-planner');
    const plannerDelete = plannerRow.querySelectorAll('button')[1];
    expect(plannerDelete).toBeDisabled();
  });

  it('creates a new role end-to-end', async () => {
    const user = userEvent.setup();
    api.roles.create.mockResolvedValue({
      id: 3,
      name: 'security',
      system_prompt: 'secure it',
      handoff_targets: [],
      is_default: false,
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
    });
    api.roles.list
      .mockResolvedValueOnce({ roles: SEED })
      .mockResolvedValueOnce({
        roles: [
          ...SEED,
          { ...SEED[1], id: 3, name: 'security', is_default: false },
        ],
      });

    render(<RolesPage />);
    await screen.findByText('planner');

    await user.click(screen.getByRole('button', { name: /new role/i }));
    await user.type(screen.getByLabelText(/^Name$/i), 'security');
    await user.type(screen.getByLabelText(/System prompt/i), 'secure it');
    await user.click(screen.getByRole('button', { name: /create role/i }));

    await waitFor(() => {
      expect(api.roles.create).toHaveBeenCalledWith({
        name: 'security',
        system_prompt: 'secure it',
        handoff_targets: [],
      });
    });
  });

  it('shows the API error detail when delete is blocked (409)', async () => {
    const user = userEvent.setup();
    api.roles.remove.mockRejectedValue(
      new ApiError("Role 'custom-auditor' is used by compositions: feature.", 409)
    );

    // Auto-confirm the window.confirm dialog.
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);

    render(<RolesPage />);
    await screen.findByText('custom-auditor');

    const row = screen.getByTestId('role-row-custom-auditor');
    const deleteBtn = row.querySelectorAll('button')[1];
    await user.click(deleteBtn);

    expect(await screen.findByRole('alert')).toHaveTextContent(
      /used by compositions/i
    );

    confirmSpy.mockRestore();
  });

  it('opens the editor with the role data when Edit is clicked', async () => {
    const user = userEvent.setup();
    render(<RolesPage />);
    await screen.findByText('custom-auditor');

    const row = screen.getByTestId('role-row-custom-auditor');
    const editBtn = row.querySelectorAll('button')[0];
    await user.click(editBtn);

    expect(screen.getByRole('heading', { name: /Edit: custom-auditor/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/^Name$/i)).toBeDisabled();
    expect(screen.getByLabelText(/System prompt/i)).toHaveValue('audit it');
  });
});
