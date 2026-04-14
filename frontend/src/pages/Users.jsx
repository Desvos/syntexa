import { useEffect, useState } from 'react';
import { usersApi } from '../api/auth.js';
import UsersTable from '../components/UsersTable.jsx';

export default function UsersPage() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newUser, setNewUser] = useState({ username: '', password: '' });
  const [creating, setCreating] = useState(false);

  // Fetch users on mount
  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await usersApi.list();
      setUsers(data.users || []);
    } catch (err) {
      setError('Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setCreating(true);
    setError('');

    try {
      await usersApi.create(newUser.username, newUser.password);
      setNewUser({ username: '', password: '' });
      setShowCreateForm(false);
      await loadUsers();
    } catch (err) {
      setError(err.message || 'Failed to create user');
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id) => {
    await usersApi.remove(id);
    await loadUsers();
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>User Management</h1>
        <button
          className="btn btn-primary"
          onClick={() => setShowCreateForm(!showCreateForm)}
        >
          {showCreateForm ? 'Cancel' : 'Create User'}
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      {showCreateForm && (
        <form className="create-form" onSubmit={handleCreate}>
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="new-username">Username (New)</label>
              <input
                id="new-username"
                type="text"
                value={newUser.username}
                onChange={(e) =>
                  setNewUser((u) => ({ ...u, username: e.target.value }))
                }
                placeholder="Enter username"
                required
                minLength={3}
              />
            </div>
            <div className="form-group">
              <label htmlFor="new-password">Password (New)</label>
              <input
                id="new-password"
                type="password"
                value={newUser.password}
                onChange={(e) =>
                  setNewUser((u) => ({ ...u, password: e.target.value }))
                }
                placeholder="Enter password"
                required
                minLength={8}
              />
            </div>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={creating}
            >
              {creating ? 'Creating...' : 'Create'}
            </button>
          </div>
        </form>
      )}

      <UsersTable
        users={users}
        onDelete={handleDelete}
        loading={loading}
      />
    </div>
  );
}
