export const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const SESSION_KEY = 'somba_session_token'

async function parseJson(res) {
  try {
    return await res.json()
  } catch {
    return null
  }
}

async function request(path, { method = 'GET', body, auth } = {}) {
  const headers = {}
  if (body) headers['Content-Type'] = 'application/json'
  if (auth) headers.Authorization = `Bearer ${auth}`

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  })
  const data = await parseJson(res)
  if (!res.ok) {
    throw new Error(data?.error?.message || 'Something went wrong. Is the API running?')
  }
  return data
}

export function getSessionToken() {
  return localStorage.getItem(SESSION_KEY)
}

export function setSessionToken(token) {
  localStorage.setItem(SESSION_KEY, token)
}

export function clearSessionToken() {
  localStorage.removeItem(SESSION_KEY)
}

export function signup({ name, email, password }) {
  return request('/v1/auth/signup', { method: 'POST', body: { name, email, password } })
}

export function login({ email, password }) {
  return request('/v1/auth/login', { method: 'POST', body: { email, password } })
}

export function fetchDashboardMe(sessionToken) {
  return request('/v1/auth/me', { auth: sessionToken })
}

export function listApiKeys(sessionToken) {
  return request('/v1/auth/api-keys', { auth: sessionToken })
}

export function createApiKey(sessionToken, name) {
  return request('/v1/auth/api-keys', { method: 'POST', auth: sessionToken, body: { name } })
}

export function revokeApiKey(sessionToken, keyRowId) {
  return request(`/v1/auth/api-keys/${keyRowId}`, { method: 'DELETE', auth: sessionToken })
}
