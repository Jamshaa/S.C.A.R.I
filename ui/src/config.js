export const getAPIBaseURL = () => {
  const host = window.location.hostname;
  const port = window.location.port;
  const protocol = window.location.protocol;
  if (host === 'localhost' || host === '127.0.0.1' || host.startsWith('127.')) {
    return `${protocol}
  }
  if (host.includes('.app.github.dev')) {
    const baseHost = host.split('-').slice(0, -2).join('-');
    return `${protocol}
  }
  if (host.includes('netlify') || host.includes('vercel')) {
    return `${protocol}
  }
  if (port) {
    return `${protocol}
  }
  return `${protocol}
};
export const API_BASE = getAPIBaseURL();
