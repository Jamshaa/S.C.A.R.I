import { API_BASE } from './config';

export const ADMIN_KEY_STORAGE_KEY = 'scari.adminKey';

const AUTH_ERROR_MESSAGE = 'Protected action blocked. Add the admin key in the sidebar or use localhost.';

const isBrowser = () => typeof window !== 'undefined';

export const getStoredAdminKey = () => {
  if (!isBrowser()) return '';
  try {
    return window.sessionStorage.getItem(ADMIN_KEY_STORAGE_KEY) || '';
  } catch {
    return '';
  }
};

export const setStoredAdminKey = (value) => {
  if (!isBrowser()) return;
  const normalized = String(value || '').trim();
  try {
    if (normalized) {
      window.sessionStorage.setItem(ADMIN_KEY_STORAGE_KEY, normalized);
    } else {
      window.sessionStorage.removeItem(ADMIN_KEY_STORAGE_KEY);
    }
  } catch {
    // Ignore storage failures and keep the key in component state only.
  }
};

export const buildApiUrl = (pathOrUrl) => (
  /^https?:\/\//i.test(pathOrUrl) ? pathOrUrl : `${API_BASE}${pathOrUrl}`
);

export const buildApiHeaders = (headers = {}) => {
  const finalHeaders = new Headers(headers);
  const adminKey = getStoredAdminKey();
  if (adminKey && !finalHeaders.has('X-API-Key')) {
    finalHeaders.set('X-API-Key', adminKey);
  }
  return finalHeaders;
};

export const getApiErrorMessage = async (response) => {
  let rawText = '';
  try {
    rawText = await response.text();
  } catch {
    rawText = '';
  }

  let detail = rawText;
  if (rawText) {
    try {
      const parsed = JSON.parse(rawText);
      detail = typeof parsed.detail === 'string' ? parsed.detail : rawText;
    } catch {
      detail = rawText;
    }
  }

  if (
    response.status === 401
    || response.status === 403
    || detail.includes('X-API-Key')
    || detail.includes('local-only')
  ) {
    return AUTH_ERROR_MESSAGE;
  }

  return detail || `Request failed: ${response.status}`;
};

export const apiFetch = async (pathOrUrl, options = {}) => {
  const response = await fetch(buildApiUrl(pathOrUrl), {
    ...options,
    headers: buildApiHeaders(options.headers),
  });
  if (!response.ok) {
    throw new Error(await getApiErrorMessage(response));
  }
  return response;
};

export const apiJsonFetch = async (pathOrUrl, options = {}) => {
  const response = await apiFetch(pathOrUrl, options);
  return response.json();
};

export const jsonRequest = (method, body, headers = {}) => ({
  method,
  headers: {
    'Content-Type': 'application/json',
    ...headers,
  },
  body: JSON.stringify(body),
});
