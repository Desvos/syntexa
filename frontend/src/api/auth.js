// Auth utilities and API client
const BASE = '/api/v1';

// Token storage key
const TOKEN_KEY = 'syntexa_auth_token';

// Get stored token
export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

// Store token
export function setToken(token) {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
}

// Remove token (logout)
export function removeToken() {
  localStorage.removeItem(TOKEN_KEY);
}

// Check if user is authenticated
export function isAuthenticated() {
  return !!getToken();
}

// Auth API
export const authApi = {
  login: async (username, password) => {
    const res = await fetch(`${BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });

    const text = await res.text();
    const data = text ? JSON.parse(text) : null;

    if (!res.ok) {
      const detail = data?.detail ?? res.statusText;
      throw new Error(detail);
    }

    // Store token on successful login
    if (data?.access_token) {
      setToken(data.access_token);
    }

    return data;
  },

  logout: async () => {
    const token = getToken();
    if (token) {
      try {
        await fetch(`${BASE}/auth/logout`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
        });
      } catch (e) {
        // Ignore logout errors
      }
    }
    removeToken();
  },
};

// User API
export const usersApi = {
  list: async () => {
    const token = getToken();
    const res = await fetch(`${BASE}/users`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error('Failed to fetch users');
    return res.json();
  },

  create: async (username, password) => {
    const token = getToken();
    const res = await fetch(`${BASE}/users`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ username, password }),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.detail || 'Failed to create user');
    }
    return res.json();
  },

  remove: async (id) => {
    const token = getToken();
    const res = await fetch(`${BASE}/users/${id}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error('Failed to delete user');
    return res.json();
  },
};

// Session expiry handling
let expiryTimer = null;

export function setSessionExpiryHandler(onExpire) {
  // Clear existing timer
  if (expiryTimer) {
    clearTimeout(expiryTimer);
    expiryTimer = null;
  }

  // Sessions expire after 24 hours (in ms)
  const SESSION_DURATION = 24 * 60 * 60 * 1000;

  expiryTimer = setTimeout(() => {
    removeToken();
    if (onExpire) onExpire();
  }, SESSION_DURATION);
}

export function clearSessionExpiryHandler() {
  if (expiryTimer) {
    clearTimeout(expiryTimer);
    expiryTimer = null;
  }
}
