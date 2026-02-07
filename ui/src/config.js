/**
 * API Configuration
 * Dynamically determines the API base URL based on the environment
 */

export const getAPIBaseURL = () => {
  const host = window.location.hostname;
  const port = window.location.port;
  const protocol = window.location.protocol;

  // Local development (localhost, 127.0.0.1)
  if (host === 'localhost' || host === '127.0.0.1' || host.startsWith('127.')) {
    return `${protocol}//${host}:8000`;
  }

  // GitHub Codespaces (format: xxx-PORTNUMBER.app.github.dev)
  if (host.includes('.app.github.dev')) {
    // Extract the base hostname (e.g., "humble-disco-wrv5rw5p7gg25656")
    const baseHost = host.split('-').slice(0, -2).join('-');
    return `${protocol}//${baseHost}-8000.app.github.dev`;
  }

  // Netlify/Vercel style: try to use /api prefix first
  if (host.includes('netlify') || host.includes('vercel')) {
    return `${protocol}//${host}/api`;
  }

  // Production - same domain, different port
  if (port) {
    return `${protocol}//${host}:8000`;
  }

  // Fallback: same domain, no port
  return `${protocol}//${host}`;
};

export const API_BASE = getAPIBaseURL();

console.log(`[SCARI] API Backend URL: ${API_BASE}`);
