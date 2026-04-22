/** T055 — component tests for the Compositions page. */
import React from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import CompositionsPage from './Compositions.jsx';

vi.mock('../api/client.js', () => {
  return {
    ApiError: class ApiError extends Error {
      constructor(msg, status) { super(msg); this.status = status; }
    },
    api: {
      roles: { list: vi.fn() },
      compositions: {
        list: vi.fn(),
        create: vi.fn(),
        update: vi.fn(),
        remove: vi.fn(),
      },
    },
  };
});

import { api, ApiError } from '../api/client.js';

const ROLES = [
  { id: 1, name: 'planner', system_prompt: '', handoff_targets: [], is_default: true, created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-01T00:00:00Z' },
  { id: 2, name: 'coder', system_prompt: '', handoff_targets: [], is_default: true, created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-01T00:00:00Z' },
  { id: 3, name: 'reviewer', system_prompt: '', handoff_targets: [], is_default: true, created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-01T00:00:00Z' },
];

const SEED = [
  {
    id: 10,
    task_type: 'feature',
    roles: ['planner', 'coder', 'reviewer'],
    max_rounds: 60,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  },
];

beforeEach(() => {
  vi.clearAllMocks();
  api.roles.list.mockResolvedValue({ roles: ROLES });
  api.compositions.list.mockResolvedValue({ compositions: SEED });
});

afterEach(() => { vi.restoreAllMocks(); });

describe('CompositionsPage', () => {
  it('lists compositions from the API with roles joined by arrows', async () => {
    render(<CompositionsPage />);
    const row = await screen.findByTestId('composition-row-feature');
    expect(row).toHaveTextContent('feature');
    expect(row).toHaveTextContent('planner → coder → reviewer');
    expect(row).toHaveTextContent('60');
  });

  it('creates a new composition end-to-end', async () => {
    const user = userEvent.setup();
    api.compositions.create.mockResolvedValue({
      id: 11,
      task_type: 'chore',
      roles: ['coder', 'reviewer'],
      max_rounds: 30,
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
    });
    api.compositions.list
      .mockResolvedValueOnce({ compositions: SEED })
      .mockResolvedValueOnce({
        compositions: [
          ...SEED,
          { id: 11, task_type: 'chore', roles: ['coder', 'reviewer'], max_rounds: 30, created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-01T00:00:00Z' },
        ],
      });

    render(<CompositionsPage />);
    await screen.findByTestId('composition-row-feature');

    await user.click(screen.getByRole('button', { name: /new composition/i }));
    await user.selectOptions(screen.getByLabelText(/task type/i), 'chore');

    // Add coder then reviewer via the free-form RoleOrder picker.
    const addRoleInput = screen.getByLabelText(/add role/i);
    await user.type(addRoleInput, 'coder{Enter}');
    await user.type(addRoleInput, 'reviewer{Enter}');

    const maxRounds = screen.getByLabelText(/max rounds/i);
    await user.clear(maxRounds);
    await user.type(maxRounds, '30');

    await user.click(screen.getByRole('button', { name: /create composition/i }));

    await waitFor(() => {
      expect(api.compositions.create).toHaveBeenCalledWith({
        task_type: 'chore',
        roles: ['coder', 'reviewer'],
        max_rounds: 30,
      });
    });
  });

  it('accepts a free-form agent type not present in the existing roles list', async () => {
    const user = userEvent.setup();
    api.compositions.create.mockResolvedValue({
      id: 12,
      task_type: 'security',
      roles: ['planner', 'security-auditor'],
      max_rounds: 60,
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
    });

    render(<CompositionsPage />);
    await screen.findByTestId('composition-row-feature');

    await user.click(screen.getByRole('button', { name: /new composition/i }));
    await user.selectOptions(screen.getByLabelText(/task type/i), 'security');

    const addRoleInput = screen.getByLabelText(/add role/i);
    await user.type(addRoleInput, 'planner{Enter}');
    // 'security-auditor' is NOT in ROLES — the picker must still accept it.
    await user.type(addRoleInput, 'security-auditor{Enter}');

    await user.click(screen.getByRole('button', { name: /create composition/i }));

    await waitFor(() => {
      expect(api.compositions.create).toHaveBeenCalledWith({
        task_type: 'security',
        roles: ['planner', 'security-auditor'],
        max_rounds: 60,
      });
    });
  });

  it('blocks submission when the pipeline is empty', async () => {
    const user = userEvent.setup();
    render(<CompositionsPage />);
    await screen.findByTestId('composition-row-feature');

    await user.click(screen.getByRole('button', { name: /new composition/i }));
    await user.selectOptions(screen.getByLabelText(/task type/i), 'fix');
    await user.click(screen.getByRole('button', { name: /create composition/i }));

    expect(await screen.findByRole('alert')).toHaveTextContent(/at least one role/i);
    expect(api.compositions.create).not.toHaveBeenCalled();
  });

  it('opens the editor with roles already populated when Edit is clicked', async () => {
    const user = userEvent.setup();
    render(<CompositionsPage />);
    await screen.findByTestId('composition-row-feature');

    const row = screen.getByTestId('composition-row-feature');
    const editBtn = row.querySelectorAll('button')[0];
    await user.click(editBtn);

    expect(screen.getByRole('heading', { name: /Edit: feature/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/task type/i)).toBeDisabled();
    const items = screen.getAllByTestId('role-order-item');
    expect(items).toHaveLength(3);
    expect(items[0]).toHaveTextContent('planner');
    expect(items[2]).toHaveTextContent('reviewer');
  });

  it('reorders roles via the down arrow control', async () => {
    const user = userEvent.setup();
    api.compositions.update.mockResolvedValue({ ...SEED[0], roles: ['coder', 'planner', 'reviewer'] });
    api.compositions.list
      .mockResolvedValueOnce({ compositions: SEED })
      .mockResolvedValueOnce({ compositions: [{ ...SEED[0], roles: ['coder', 'planner', 'reviewer'] }] });

    render(<CompositionsPage />);
    await screen.findByTestId('composition-row-feature');

    const editBtn = screen.getByTestId('composition-row-feature').querySelectorAll('button')[0];
    await user.click(editBtn);

    // Move planner (idx 0) down one slot → coder, planner, reviewer.
    await user.click(screen.getByRole('button', { name: /move planner down/i }));
    await user.click(screen.getByRole('button', { name: /^save$/i }));

    await waitFor(() => {
      expect(api.compositions.update).toHaveBeenCalledWith(10, {
        roles: ['coder', 'planner', 'reviewer'],
        max_rounds: 60,
      });
    });
  });

  it('shows API error detail when delete is blocked (409)', async () => {
    const user = userEvent.setup();
    api.compositions.remove.mockRejectedValue(
      new ApiError('Composition is referenced by an active swarm.', 409)
    );
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);

    render(<CompositionsPage />);
    await screen.findByTestId('composition-row-feature');

    const row = screen.getByTestId('composition-row-feature');
    const deleteBtn = row.querySelectorAll('button')[1];
    await user.click(deleteBtn);

    expect(await screen.findByRole('alert')).toHaveTextContent(/active swarm/i);

    confirmSpy.mockRestore();
  });
});
