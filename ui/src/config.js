export const getAPIBaseURL = () => {
  const host = window.location.hostname;
  const port = window.location.port;
  const protocol = window.location.protocol;

  if (host === "localhost" || host === "127.0.0.1" || host.startsWith("127.")) {
    return `${protocol}//${host}:8000`;
  }

  if (host.includes(".app.github.dev")) {
    const baseHost = host.split("-").slice(0, -2).join("-");
    return `${protocol}//${baseHost}-8000.app.github.dev`;
  }

  if (host.includes("netlify") || host.includes("vercel")) {
    return `${protocol}//${host}/api`;
  }

  if (port) {
    return `${protocol}//${host}:${port}`;
  }

  return `${protocol}//${host}`;
};

export const API_BASE = getAPIBaseURL();