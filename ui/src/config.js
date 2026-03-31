const trimTrailingSlash = (value) => value.replace(/\/+$/, '');

export const getAPIBaseURL = () => {
  const envBase = import.meta.env.VITE_API_BASE?.trim();
  if (envBase) {
    return trimTrailingSlash(envBase);
  }

  const host = window.location.hostname;
  const protocol = window.location.protocol;

  if (host === 'localhost' || host === '127.0.0.1' || host.startsWith('127.')) {
    return `${protocol}//${host}:8000`;
  }

  if (host.includes('.app.github.dev')) {
    const baseHost = host.split('-').slice(0, -2).join('-');
    return `${protocol}//${baseHost}-8000.app.github.dev`;
  }

  if (host.includes('netlify') || host.includes('vercel')) {
    return `${protocol}//${host}/api`;
  }

  return `${protocol}//${host}:8000`;
};

export const API_BASE = getAPIBaseURL();

export const TRAINING_CONFIG_BY_MODE = {
  AIR: 'configs/default.yaml',
  LIQUID: 'configs/liquid.yaml',
  HYBRID: 'configs/hybrid.yaml',
};

export const getTrainingConfigForMode = (mode = 'AIR') => (
  TRAINING_CONFIG_BY_MODE[String(mode || 'AIR').toUpperCase()] || TRAINING_CONFIG_BY_MODE.AIR
);
