import { apiFetch } from './apiClient';

export const fetchWithRetry = async (url, options = {}, retries = 3) => {
  for (let i = 0; i < retries; i += 1) {
    try {
      return await apiFetch(url, options);
    } catch (error) {
      if (error.name === 'AbortError') {
        return null;
      }
      if (i === retries - 1) {
        throw error;
      }
      await new Promise((resolve) => {
        setTimeout(resolve, 1000 * (i + 1));
      });
    }
  }
  return null;
};

export const fmtSteps = (value) => {
  if (value >= 1_000_000) {
    return `${(value / 1_000_000).toFixed(value % 1_000_000 === 0 ? 0 : 1)}M`;
  }
  if (value >= 1_000) {
    return `${(value / 1_000).toFixed(0)}k`;
  }
  return value.toString();
};

export const getSavingsBasisLabel = (value) => (
  value === 'non_it_overhead' ? 'overhead save' : 'save'
);

export const getComparisonStats = (baseline = {}, candidate = {}) => {
  const baselinePower = Number(baseline.total_power_consumption || 0);
  const candidatePower = Number(candidate.total_power_consumption || baselinePower);
  const baselineIt = Number(baseline.total_it_power_consumption || 0);
  const candidateIt = Number(candidate.total_it_power_consumption || 0);
  const baselineOverhead = Math.max(0, baselinePower - baselineIt);
  const candidateOverhead = Math.max(0, candidatePower - candidateIt);
  const baselineCooling = Number(baseline.total_cooling_power_consumption || baselineOverhead);
  const candidateCooling = Number(candidate.total_cooling_power_consumption || candidateOverhead);
  const totalSavingsPct = baselinePower > 0 ? ((baselinePower - candidatePower) / baselinePower) * 100 : 0;
  const overheadSavingsPct = baselineOverhead > 0
    ? ((baselineOverhead - candidateOverhead) / baselineOverhead) * 100
    : totalSavingsPct;
  const coolingSavingsPct = baselineCooling > 0
    ? ((baselineCooling - candidateCooling) / baselineCooling) * 100
    : overheadSavingsPct;
  const baselinePue = Number(baseline.average_pue || 0);
  const candidatePue = Number(candidate.average_pue || baselinePue);
  const baselinePueOverhead = Math.max(0, baselinePue - 1.0);
  const candidatePueOverhead = Math.max(0, candidatePue - 1.0);
  const pueOverheadReductionPct = baselinePueOverhead > 0
    ? ((baselinePueOverhead - candidatePueOverhead) / baselinePueOverhead) * 100
    : totalSavingsPct;
  return { totalSavingsPct, overheadSavingsPct, coolingSavingsPct, pueOverheadReductionPct };
};

export const inferEvaluationConfig = (modelName = '') => {
  const normalized = modelName.toLowerCase();
  if (normalized.includes('liquid') || normalized.includes('water') || normalized.includes('hydro')) {
    return 'configs/liquid.yaml';
  }
  if (normalized.includes('hybrid')) {
    return 'configs/hybrid.yaml';
  }
  return 'configs/default.yaml';
};

export const formatConfigLabel = (config = '') => config.replace(/\\/g, '/').replace(/^.*?(configs\/)/, '$1');

export const formatCoolingMode = (mode = '') => {
  const normalized = String(mode || '').toUpperCase();
  if (normalized === 'LIQUID') {
    return 'Liquid';
  }
  if (normalized === 'HYBRID') {
    return 'Hybrid';
  }
  return 'Air';
};

export const getScenarioLabel = (context = {}) => formatConfigLabel(context.config || 'configs/default.yaml');

export const getOverrideDependence = (rate) => {
  if (rate < 5) {
    return { label: 'Low', tone: 'var(--success)' };
  }
  if (rate < 15) {
    return { label: 'Moderate', tone: 'var(--warning)' };
  }
  return { label: 'High', tone: 'var(--danger)' };
};

export const buildEvaluationStory = (baseline = {}, candidate = {}, context = {}) => {
  const { totalSavingsPct } = getComparisonStats(baseline, candidate);
  const safetyViolations = Number(candidate.safety_violations || 0);
  const overrideRate = Number(candidate.safety_override_rate_percent || 0);
  const overrideTone = getOverrideDependence(overrideRate);
  const safe = safetyViolations === 0;
  if (totalSavingsPct > 0 && safe) {
    return {
      headline: 'SCARI beat the baseline safely',
      kicker: `${totalSavingsPct.toFixed(2)}% lower total facility power in ${getScenarioLabel(context)}.`,
      tone: 'var(--success)',
      overrideTone,
    };
  }
  if (totalSavingsPct > 0 && !safe) {
    return {
      headline: 'SCARI saved energy but lost thermal safety',
      kicker: `${totalSavingsPct.toFixed(2)}% savings, but ${safetyViolations} safety violations were recorded.`,
      tone: 'var(--warning)',
      overrideTone,
    };
  }
  if (safe) {
    return {
      headline: 'SCARI stayed safe but did not beat the baseline',
      kicker: `No thermal violations, but savings versus baseline were ${totalSavingsPct.toFixed(2)}%.`,
      tone: 'var(--text)',
      overrideTone,
    };
  }
  return {
    headline: 'SCARI did not close the run successfully',
    kicker: `The evaluation under ${getScenarioLabel(context)} requires manual review.`,
    tone: 'var(--danger)',
    overrideTone,
  };
};

export const downloadFileFromApi = async (url, filename, addToast) => {
  try {
    const response = await apiFetch(url);
    const blob = await response.blob();
    const objectUrl = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = objectUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(objectUrl);
    addToast(`Downloaded ${filename}`, 'success');
  } catch (error) {
    addToast(`Download failed: ${error.message}`, 'error');
  }
};

export const CHART_LABELS = {
  temperature_comparison: {
    title: 'Temperature Over Time',
    desc: 'Server temperatures: baseline PID vs SCARI agent',
  },
  power_comparison: {
    title: 'Power Consumption',
    desc: 'Total electrical power usage comparison',
  },
  cooling_efficiency: {
    title: 'Cooling Efficiency',
    desc: 'PUE and cooling energy overhead per step',
  },
  performance_dashboard: {
    title: 'Performance Dashboard',
    desc: 'Summary of all key metrics in one view',
  },
  reward_analysis: {
    title: 'Agent Reward',
    desc: 'Cumulative reward signal during evaluation',
  },
};

export const getChartLabel = (imgPath) => {
  const match = Object.entries(CHART_LABELS).find(([key]) => imgPath.toLowerCase().includes(key));
  if (match) {
    return match[1];
  }
  return { title: 'Analysis Chart', desc: 'Evaluation metric visualisation' };
};
