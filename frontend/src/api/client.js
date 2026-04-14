const BASE = '/api/v1';

async function request(path, { method = 'GET', body } = {}) {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
    credentials: 'include',
  });
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
