import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import UsersPage from './Users.jsx';

const mockUsers = [
  { id: 1, username: 'admin', created_at: '2026-04-14T10:00:00Z', last_login_at: '2026-04-14T12:00:00Z' },
  { id: 2, username: 'user1', created_at: '2026-04-14T11:00:00Z', last_login_at: null },
];

vi.mock('../api/auth.js', () => ({
  usersApi: {
    list: vi.fn(),
    create: vi.fn(),
    remove: vi.fn(),
  },
}));

import { usersApi } from '../api/auth.js';

describe('UsersPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state initially', () => {
    usersApi.list.mockImplementation(() => new Promise(() => {})); // Never resolves

    render(<UsersPage />);

    expect(screen.getByText(/loading users/i)).toBeInTheDocument();
  });

  it('renders users after loading', async () => {
    usersApi.list.mockResolvedValueOnce({ users: mockUsers });

    render(<UsersPage />);

    await waitFor(() => {
      expect(screen.getByText('admin')).toBeInTheDocument();
    });

    expect(screen.getByText('user1')).toBeInTheDocument();
  });

  it('shows empty state when no users', async () => {
    usersApi.list.mockResolvedValueOnce({ users: [] });

    render(<UsersPage />);

    await waitFor(() => {
      expect(screen.getByText(/no users found/i)).toBeInTheDocument();
    });
  });

  it('shows error when loading fails', async () => {
    usersApi.list.mockRejectedValueOnce(new Error('Failed to fetch'));

    render(<UsersPage />);

    await waitFor(() => {
      expect(screen.getByText(/failed to load users/i)).toBeInTheDocument();
    });
  });

  it('toggles create form when button is clicked', async () => {
    usersApi.list.mockResolvedValueOnce({ users: mockUsers });

    render(<UsersPage />);

    await waitFor(() => {
      expect(screen.getByText('admin')).toBeInTheDocument();
    });

    const createButton = screen.getByRole('button', { name: /create user/i });
    await userEvent.click(createButton);

    expect(screen.getByLabelText(/username.*new/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password.*new/i)).toBeInTheDocument();
  });

  it('calls create API when submitting form', async () => {
    usersApi.list.mockResolvedValue({ users: mockUsers });
    usersApi.create.mockResolvedValueOnce({ id: 3, username: 'newuser' });

    render(<UsersPage />);

    await waitFor(() => {
      expect(screen.getByText('admin')).toBeInTheDocument();
    });

    await userEvent.click(screen.getByRole('button', { name: /create user/i }));

    await userEvent.type(screen.getByLabelText(/username.*new/i), 'newuser');
    await userEvent.type(screen.getByLabelText(/password.*new/i), 'password123');

    await userEvent.click(screen.getByRole('button', { name: /^create$/i }));

    await waitFor(() => {
      expect(usersApi.create).toHaveBeenCalledWith('newuser', 'password123');
    });
  });

  it('calls delete API when clicking delete button', async () => {
    usersApi.list.mockResolvedValueOnce({ users: mockUsers });
    usersApi.remove.mockResolvedValueOnce({});

    window.confirm = vi.fn(() => true);

    render(<UsersPage />);

    await waitFor(() => {
      expect(screen.getByText('user1')).toBeInTheDocument();
    });

    const deleteButtons = screen.getAllByRole('button', { name: /delete/i });
    await userEvent.click(deleteButtons[1]); // Delete user1

    await waitFor(() => {
      expect(usersApi.remove).toHaveBeenCalledWith(2);
    });
  });
});
