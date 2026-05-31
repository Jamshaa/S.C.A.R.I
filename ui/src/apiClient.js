import { API_BASE } from './config';

export const buildApiUrl = (pathOrUrl) => (
  /^https?:\/\//i.test(pathOrUrl) ? pathOrUrl : `${API_BASE}${pathOrUrl}`
);

export const buildApiHeaders = (headers = {}) => new Headers(headers);

export const getApiErrorMessage = async (response) => {
  try {
    const text = await response.text();
    try {
      const parsed = JSON.parse(text);
      return typeof parsed.detail === 'string' ? parsed.detail : text;
    } catch {
      return text || `Request failed: ${response.status}`;
    }
  } catch {
    return `Request failed: ${response.status}`;
  }
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
