import { getToken, removeToken } from './auth.js';

const BASE = '/api/v1';

// Event emitter for auth errors (401 handling)
let authErrorHandler = null;

export function setAuthErrorHandler(handler) {
  authErrorHandler = handler;
}

async function request(path, { method = 'GET', body } = {}) {
  const token = getToken();
  const headers = {};

  if (body) {
    headers['Content-Type'] = 'application/json';
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: Object.keys(headers).length > 0 ? headers : undefined,
    body: body ? JSON.stringify(body) : undefined,
    credentials: 'include',
  });

  // Handle 401 Unauthorized - token invalid or expired
  if (res.status === 401) {
    removeToken();
    // Force full page redirect to clear React state and go to login
    window.location.replace('/login');
    // Return a pending promise that never resolves (page will reload)
    return new Promise(() => {});
  }

  if (res.status === 204) return null;
  const text = await res.text();
  const data = text ? JSON.parse(text) : null;
  if (!res.ok) {
    const detail = data?.detail ?? res.statusText;
    throw new ApiError(detail, res.status, data);
  }
  return data;
}

export class ApiError extends Error {
  constructor(message, status, data) {
    super(typeof message === 'string' ? message : JSON.stringify(message));
    this.status = status;
    this.data = data;
  }
}

export const api = {
  roles: {
    list: () => request('/roles'),
    create: (payload) => request('/roles', { method: 'POST', body: payload }),
    update: (id, payload) => request(`/roles/${id}`, { method: 'PUT', body: payload }),
    remove: (id) => request(`/roles/${id}`, { method: 'DELETE' }),
  },
  compositions: {
    list: () => request('/compositions'),
    create: (payload) => request('/compositions', { method: 'POST', body: payload }),
    update: (id, payload) => request(`/compositions/${id}`, { method: 'PUT', body: payload }),
    remove: (id) => request(`/compositions/${id}`, { method: 'DELETE' }),
  },
  settings: {
    get: () => request('/settings'),
    update: (payload) => request('/settings', { method: 'PATCH', body: payload }),
    status: () => request('/settings/status'),
  },
  swarms: {
    active: () => request('/swarms/active'),
    completed: (limit = 50) => request(`/swarms/completed?limit=${limit}`),
    log: (id) => request(`/swarms/${id}/log`),
  },
};
