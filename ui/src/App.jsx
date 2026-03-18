import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Activity, Play, BarChart3,
  RefreshCw, AlertCircle, CheckCircle2, Loader2,
  History, BarChart, Edit2, X, Sun, Moon, Trash2, Leaf,
  ChevronRight, Download, Cpu, Zap, ThermometerSun,
  Shield, TrendingDown, TreePine, Minus, Plus, Image,
  Droplets, Wind, GitMerge, Globe
} from 'lucide-react';
import DataCenterCalculator from './DataCenterCalculator';
import GlobalEmissions from './GlobalEmissions';
import { API_BASE } from './config';
const fetchWithRetry = async (url, options = {}, retries = 3) => {
  for (let i = 0; i < retries; i++) {
    try {
      const res = await fetch(url, options);
      if (res.ok) return res;
      if (res.status >= 400 && res.status < 500) throw new Error(await res.text());
      throw new Error(`Request failed: ${res.status}`);
    } catch (e) {
      if (e.name === 'AbortError') return null;
      if (i === retries - 1) throw e;
      await new Promise(r => setTimeout(r, 1000 * (i + 1)));
    }
  }
};
const fmtSteps = (n) => {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(n % 1_000_000 === 0 ? 0 : 1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}k`;
  return n.toString();
};
const normalizeBaselineLabel = (value) => {
  const raw = (value || 'BASELINE').trim();
  return raw.toUpperCase() === 'REAL_WORLD_PID' ? 'BASELINE' : raw;
};
const getSavingsBasisLabel = (value) => (
  value === 'non_it_overhead' ? 'overhead save' : 'save'
);
const getComparisonStats = (baseline = {}, candidate = {}) => {
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
const StepperInput = ({ value, onChange, step = 1000, min = 0, max = Infinity, presets = [] }) => {
  const intervalRef = useRef(null);
  const timeoutRef = useRef(null);
  const clamp = (v) => Math.max(min, Math.min(max, v));
  const startHoldSafe = (delta) => {
    onChange(clamp(value + delta));
    timeoutRef.current = setTimeout(() => {
      intervalRef.current = setInterval(() => {
        valueRef.current = clamp(valueRef.current + delta);
        onChange(valueRef.current);
      }, 80);
    }, 400);
  };
  const stopHold = () => {
    clearTimeout(timeoutRef.current);
    clearInterval(intervalRef.current);
  };
  const valueRef = useRef(value);
  useEffect(() => { valueRef.current = value; }, [value]);
  const [inputValue, setInputValue] = useState(fmtSteps(value));
  useEffect(() => {
    setInputValue(fmtSteps(value));
  }, [value]);
  const handleInputChange = (e) => {
    setInputValue(e.target.value);
  };
  const handleInputBlur = () => {
    let raw = inputValue.toLowerCase();
    let val = parseFloat(raw);
    if (raw.endsWith('m')) val *= 1_000_000;
    else if (raw.endsWith('k')) val *= 1_000;
    if (isNaN(val)) {
      setInputValue(fmtSteps(value));
    } else {
      const clamped = clamp(val);
      onChange(clamped);
      setInputValue(fmtSteps(clamped));
    }
  };
  const handleKeyDown = (e) => {
    if (e.key === 'Enter') handleInputBlur();
  };
  return (
    <div>
      <div className="stepper">
        <button
          className="stepper-btn"
          onMouseDown={() => startHoldSafe(-step)}
          onMouseUp={stopHold}
          onMouseLeave={stopHold}
          tabIndex={-1}
        >
          <Minus size={14} />
        </button>
        <input
          type="text"
          className="stepper-input-field"
          value={inputValue}
          onChange={handleInputChange}
          onBlur={handleInputBlur}
          onKeyDown={handleKeyDown}
        />
        <button
          className="stepper-btn"
          onMouseDown={() => startHoldSafe(step)}
          onMouseUp={stopHold}
          onMouseLeave={stopHold}
          tabIndex={-1}
        >
          <Plus size={14} />
        </button>
      </div>
      {presets.length > 0 && (
        <div className="preset-grid">
          {presets.map(p => (
            <button
              key={p}
              className={`preset-pill ${value === p ? 'active' : ''}`}
              onClick={() => onChange(p)}
            >
              {fmtSteps(p)}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};
const CHART_LABELS = {
  'temperature_comparison': { title: 'Temperature Over Time', desc: 'Server temperatures: baseline PID vs SCARI agent' },
  'power_comparison': { title: 'Power Consumption', desc: 'Total electrical power usage comparison' },
  'cooling_efficiency': { title: 'Cooling Efficiency', desc: 'PUE and cooling energy overhead per step' },
  'performance_dashboard': { title: 'Performance Dashboard', desc: 'Summary of all key metrics in one view' },
  'reward_analysis': { title: 'Agent Reward', desc: 'Cumulative reward signal during evaluation' },
};
const getChartLabel = (imgPath) => {
  for (const [key, label] of Object.entries(CHART_LABELS)) {
    if (imgPath.toLowerCase().includes(key)) return label;
  }
  return { title: `Analysis Chart`, desc: 'Evaluation metric visualisation' };
};
const Toast = ({ message, type }) => (
  <div className={`toast animate-slide-up ${type}`}>
    {type === 'success'
      ? <CheckCircle2 size={15} color="var(--success)" />
      : <AlertCircle size={15} color="var(--danger)" />}
    <span>{message}</span>
  </div>
);
const App = () => {
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState('');
  const [isTraining, setIsTraining] = useState(false);
  const [trainingSteps, setTrainingSteps] = useState(600000);
  const [trainingName, setTrainingName] = useState('scari_thermal_safe');
  const [coolingMode, setCoolingMode] = useState('AIR');
  const [trainingProgress, setTrainingProgress] = useState(0);
  const [lastLog, setLastLog] = useState('');
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [evalSteps, setEvalSteps] = useState(5000);
  const [evalName, setEvalName] = useState('eval_optimization');
  const [evalLog, setEvalLog] = useState('');
  const [results, setResults] = useState(null);
  const [evalHistory, setEvalHistory] = useState([]);
  const [loadingEvalHistory, setLoadingEvalHistory] = useState(false);
  const [selectedDecision, setSelectedDecision] = useState(null);
  const [isRenaming, setIsRenaming] = useState(false);
  const [renameTarget, setRenameTarget] = useState('');
  const [newName, setNewName] = useState('');
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState('');
  const [toasts, setToasts] = useState([]);
  const [isCompareModalOpen, setIsCompareModalOpen] = useState(false);
  const [compareSelections, setCompareSelections] = useState({ air: '', liquid: '', hybrid: '' });
  const [theme, setTheme] = useState(() =>
    window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  );
  const [mainTab, setMainTab] = useState('analytics');
  const isTrainingRef = useRef(isTraining);
  const isEvaluatingRef = useRef(isEvaluating);
  useEffect(() => { isTrainingRef.current = isTraining; }, [isTraining]);
  useEffect(() => { isEvaluatingRef.current = isEvaluating; }, [isEvaluating]);
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);
  const toggleTheme = () => setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  const addToast = useCallback((message, type = 'success') => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 3500);
  }, []);
  const fetchModels = useCallback(() => {
    fetch(`${API_BASE}/models`)
      .then(res => res.json())
      .then(data => setModels(data.models || []))
      .catch((error) => addToast(`Failed to fetch models: ${error.message}`, 'error'));
  }, [addToast]);
  const fetchEvalHistory = useCallback(() => {
    setLoadingEvalHistory(true);
    fetch(`${API_BASE}/history`)
      .then(res => res.json())
      .then(data => setEvalHistory(data.history || []))
      .catch((error) => addToast(`Failed to fetch evaluation history: ${error.message}`, 'error'))
      .finally(() => setLoadingEvalHistory(false));
  }, [addToast]);
  const fetchResults = useCallback(async () => {
    try {
      const res = await fetchWithRetry(`${API_BASE}/evaluation-results`);
      if (!res) return;
      const data = await res.json();
      if (data.metrics) setResults(data);
    } catch (error) {
      console.debug('Failed to fetch latest evaluation results', error);
    }
  }, []);
  const fetchStatus = useCallback(async () => {
    try {
      const [statusRes, evalRes] = await Promise.all([
        fetchWithRetry(`${API_BASE}/status`),
        fetchWithRetry(`${API_BASE}/evaluation-status`)
      ]);
      if (statusRes) {
        const sd = await statusRes.json();
        if (sd.is_training) {
          setIsTraining(true);
          setTrainingProgress(sd.progress || 0);
          setLastLog(sd.last_log || '');
        } else if (isTrainingRef.current) {
          setIsTraining(false);
          setTrainingProgress(0);
          fetchModels();
        }
      }
      if (evalRes) {
        const ed = await evalRes.json();
        if (ed.is_evaluating) {
          setIsEvaluating(true);
          setEvalLog(ed.last_log || '');
        } else if (isEvaluatingRef.current) {
          setIsEvaluating(false);
          setEvalLog('');
          fetchResults();
          fetchEvalHistory();
        }
      }
    } catch (error) {
      console.debug('Status polling failed', error);
    }
  }, [fetchEvalHistory, fetchModels, fetchResults]);
  useEffect(() => {
    fetchModels();
    fetchEvalHistory();
    let isMounted = true;
    let errorCount = 0;
    const poll = async () => {
      if (!isMounted) return;
      try {
        await fetchStatus();
        errorCount = 0; 
      } catch (error) {
        errorCount++;
        console.debug('Polling iteration failed', error);
        if (errorCount > 5) {
          console.error("Polling stopped due to consecutive errors.");
          addToast("Connection to backend lost. Polling stopped.", "error");
          return;
        }
      }
      if (isMounted) {
        const delay = Math.min(2000 * Math.pow(1.2, errorCount), 10000);
        setTimeout(poll, delay);
      }
    };
    const timeout = setTimeout(poll, 2000);
    return () => {
      isMounted = false;
      clearTimeout(timeout);
    };
  }, [addToast, fetchEvalHistory, fetchModels, fetchStatus]);
  const loadEvalResult = async (runId) => {
    try {
      const res = await fetch(`${API_BASE}/history/${runId}`);
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setResults(data);
      addToast(`Loaded evaluation: ${runId}`, 'success');
      setMainTab('analytics');
    } catch (e) {
      addToast(`Failed to load: ${e.message}`, 'error');
    }
  };
  const deleteEvalResult = async (runId, e) => {
    if (e) e.stopPropagation();
    if (!window.confirm(`Delete evaluation ${runId}?`)) return;
    try {
      const res = await fetch(`${API_BASE}/history/${runId}`, { method: 'DELETE' });
      if (!res.ok) throw new Error(await res.text());
      setEvalHistory(prev => prev.filter(h => h.id !== runId));
      addToast('Evaluation deleted', 'success');
    } catch (error) {
      addToast(`Delete failed: ${error.message}`, 'error');
    }
  };
  const handleTrain = async () => {
    try {
      const res = await fetch(`${API_BASE}/train`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          timesteps: trainingSteps,
          name: trainingName,
          config: 'configs/default.yaml',
          cooling_mode: coolingMode
        })
      });
      if (!res.ok) throw new Error(await res.text());
      setIsTraining(true);
      setTrainingProgress(0);
      addToast(`Training started (${coolingMode} cooling)`);
    } catch (e) {
      addToast(e.message || 'Training failed', 'error');
    }
  };
  const handleRunComparison = async () => {
    const { air, liquid, hybrid } = compareSelections;
    if (!air || !liquid || !hybrid) {
      addToast('Please select all three models for comparison', 'error');
      return;
    }
    setIsCompareModalOpen(false);
    setIsEvaluating(true);
    setEvalLog('Requesting comparative evaluation…');
    try {
      const res = await fetch(`${API_BASE}/evaluate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: 'MULTI', 
          models: [air, liquid, hybrid],
          steps: evalSteps,
          name: evalName
        })
      });
      if (!res.ok) throw new Error(await res.text());
      addToast(`Comparing: ${air}, ${liquid}, ${hybrid}`);
    } catch (e) {
      addToast(e.message || 'Evaluation failed', 'error');
      setIsEvaluating(false);
    }
  };
  const handleEvaluate = async () => {
    if (!selectedModel) {
      addToast('Select a model first', 'error');
      return;
    }
    setIsEvaluating(true);
    setEvalLog('Requesting evaluation…');
    try {
      const res = await fetch(`${API_BASE}/evaluate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: selectedModel,
          steps: evalSteps,
          name: evalName
        })
      });
      if (!res.ok) throw new Error(await res.text());
      setIsEvaluating(true);
      setEvalLog('');
      addToast(`Evaluating ${selectedModel}`);
    } catch (e) {
      addToast(e.message || 'Evaluation failed', 'error');
    }
  };
  const handleRename = async () => {
    if (!newName.trim()) return;
    try {
      const res = await fetch(`${API_BASE}/models/rename`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ old_name: renameTarget, new_name: newName })
      });
      if (!res.ok) throw new Error(await res.text());
      addToast('Model renamed', 'success');
      const finalName = newName.endsWith('.zip') ? newName : `${newName}.zip`;
      setModels(prev => prev.map(m => m === renameTarget ? finalName : m));
      if (selectedModel === renameTarget) setSelectedModel(finalName);
      setIsRenaming(false);
      setNewName('');
    } catch (e) {
      addToast(e.message || 'Rename failed', 'error');
    }
  };
  const handleRequestDelete = (modelName, e) => {
    e.stopPropagation();
    setDeleteTarget(modelName);
    setIsDeleting(true);
  };
  const handleRequestDeleteAll = () => {
    setDeleteTarget('ALL');
    setIsDeleting(true);
  };
  const confirmDelete = async () => {
    if (!deleteTarget) return;
    if (deleteTarget === 'ALL') {
      try {
        const res = await fetch(`${API_BASE}/models`, { method: 'DELETE' });
        if (!res.ok) throw new Error(await res.text());
        const data = await res.json();
        addToast(data.message || 'All models deleted', 'success');
        setModels([]);
        setSelectedModel('');
      } catch (error) {
        addToast(`Failed to delete all models: ${error.message}`, 'error');
      }
    } else {
      try {
        const res = await fetch(`${API_BASE}/models/${deleteTarget}`, { method: 'DELETE' });
        if (!res.ok) throw new Error(await res.text());
        addToast(`Deleted ${deleteTarget}`, 'success');
        setModels(prev => prev.filter(m => m !== deleteTarget));
        if (selectedModel === deleteTarget) setSelectedModel('');
      } catch (error) {
        addToast(`Failed to delete model: ${error.message}`, 'error');
      }
    }
    setIsDeleting(false);
    setDeleteTarget('');
  };
  const downloadChart = async (imgUrl, filename) => {
    try {
      const res = await fetch(`${API_BASE}${imgUrl}`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      addToast(`Downloaded ${filename}`);
    } catch (error) {
      addToast(`Download failed: ${error.message}`, 'error');
    }
  };
  const downloadAllCharts = async () => {
    if (!results?.images) return;
    for (let i = 0; i < results.images.length; i++) {
      await downloadChart(results.images[i], `scari_chart_${i + 1}.png`);
    }
  };
  const ModalOverlay = ({ children }) => (
    <div style={{
      position: 'fixed', inset: 0,
      background: theme === 'dark' ? 'rgba(0,0,0,0.7)' : 'rgba(0,0,0,0.3)',
      backdropFilter: 'blur(4px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000
    }}>
      {children}
    </div>
  );
  return (
    <div className="app-container">
      {isDeleting && (
        <ModalOverlay>
          <div className="card animate-fade-in" style={{
            width: '420px', padding: '28px',
            border: '1px solid var(--danger)', margin: 0,
            boxShadow: 'var(--shadow-lg)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px', color: 'var(--danger)' }}>
              <AlertCircle size={20} />
              <h3 style={{ textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Confirm Deletion
              </h3>
            </div>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '24px', lineHeight: 1.6 }}>
              {deleteTarget === 'ALL'
                ? 'Delete ALL models? This action cannot be undone.'
                : <span>Delete <strong style={{ color: 'var(--text)' }}>{deleteTarget}</strong>? This cannot be undone.</span>
              }
            </p>
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
              <button className="btn btn-outline" onClick={() => setIsDeleting(false)}>Cancel</button>
              <button className="btn btn-danger" onClick={confirmDelete}>
                {deleteTarget === 'ALL' ? 'Wipe Registry' : 'Delete'}
              </button>
            </div>
          </div>
        </ModalOverlay>
      )}
      {isRenaming && (
        <ModalOverlay>
          <div className="card animate-fade-in" style={{ width: '400px', padding: '28px', margin: 0, boxShadow: 'var(--shadow-lg)' }}>
            <h3 style={{ textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '3px' }}>
              Rename Model
            </h3>
            <p style={{ fontSize: '12px', color: 'var(--muted)', marginBottom: '16px' }}>{renameTarget}</p>
            <input
              value={newName}
              onChange={e => setNewName(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleRename()}
              placeholder="new_identifier"
              autoFocus
            />
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
              <button className="btn btn-outline" onClick={() => setIsRenaming(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={handleRename}>Update</button>
            </div>
          </div>
        </ModalOverlay>
      )}
      <aside className="sidebar">
        <div className="sidebar-section" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <h1 style={{ letterSpacing: '-0.05em', fontSize: '24px' }}>S.C.A.R.I</h1>
            <p style={{
              fontSize: '9px', textTransform: 'uppercase', letterSpacing: '0.18em',
              fontWeight: 700, color: 'var(--muted)', marginTop: '3px'
            }}>
              Cooling Intelligence
            </p>
          </div>
          <button
            className="btn btn-ghost"
            onClick={toggleTheme}
            title={theme === 'dark' ? 'Light mode' : 'Dark mode'}
          >
            {theme === 'dark' ? <Sun size={15} /> : <Moon size={15} />}
          </button>
        </div>
        <section className="sidebar-section">
          <div className="card-title">
            <Cpu size={11} />
            Training
          </div>
          <div>
            <label>Run Identifier</label>
            <input
              value={trainingName}
              onChange={e => setTrainingName(e.target.value)}
              placeholder="run_01"
            />
            <label>Timesteps</label>
            <StepperInput
              value={trainingSteps}
              onChange={setTrainingSteps}
              step={50000}
              min={1000}
              max={10000000}
              presets={[100000, 300000, 600000, 1000000]}
            />
            <label style={{ marginTop: '10px' }}>Cooling Mode</label>
            <div style={{ display: 'flex', gap: '6px', marginBottom: '8px' }}>
              {[
                { id: 'AIR', icon: Wind, label: 'Air', cost: '€150' },
                { id: 'LIQUID', icon: Droplets, label: 'Water', cost: '€850' },
                { id: 'HYBRID', icon: GitMerge, label: 'Hybrid', cost: '€500' },
              ].map(m => (
                <button
                  key={m.id}
                  className={`preset-pill ${coolingMode === m.id ? 'active' : ''}`}
                  onClick={() => setCoolingMode(m.id)}
                  style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '3px', padding: '8px 4px' }}
                >
                  <m.icon size={14} />
                  <span style={{ fontSize: '10px', fontWeight: 600 }}>{m.label}</span>
                </button>
              ))}
            </div>
            <div style={{
              fontSize: '10px', color: 'var(--muted)', padding: '6px 8px',
              background: 'var(--surface-raised)', borderRadius: 'var(--radius)',
              border: '1px solid var(--border)', marginBottom: '8px', lineHeight: 1.6
            }}>
              {coolingMode === 'AIR' && '💨 Traditional forced-air · €150/srv CAPEX · PUE ~1.4'}
              {coolingMode === 'LIQUID' && '💧 Direct liquid cooling · €850/srv CAPEX · PUE ~1.05'}
              {coolingMode === 'HYBRID' && '⚡ Air + Liquid hybrid · €500/srv CAPEX · PUE ~1.15'}
            </div>
            <button
              className="btn btn-primary"
              style={{ width: '100%', marginTop: '4px' }}
              onClick={handleTrain}
              disabled={isTraining}
            >
              {isTraining ? <Loader2 size={13} className="spin" /> : <Play size={13} />}
              {isTraining ? 'Training…' : 'Start Training'}
            </button>
          </div>
        </section>
        {isTraining && (
          <div style={{ marginBottom: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
              <span className="text-label">Progress</span>
              <span style={{ fontSize: '11px', fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--text)' }}>
                {trainingProgress}%
              </span>
            </div>
            <div className="progress-track">
              <div className="progress-fill" style={{
                width: `${trainingProgress}%`,
                background: 'var(--accent)'
              }} />
            </div>
            <p style={{
              fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--muted)',
              marginTop: '6px', lineHeight: 1.5, maxHeight: '40px', overflow: 'hidden'
            }}>
              {lastLog || '> Initialising…'}
            </p>
          </div>
        )}
        <section className="sidebar-section registry-section">
          <div className="card-title" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Activity size={11} />
              Registry
            </span>
            <button className="btn btn-ghost" onClick={fetchModels} style={{ padding: '3px' }}>
              <RefreshCw size={11} />
            </button>
          </div>
          <div className="registry-controls">
            <label>Run Name</label>
            <input
              value={evalName}
              onChange={e => setEvalName(e.target.value)}
              placeholder="eval_optimization"
              style={{ marginBottom: '8px' }}
            />
            <label>Eval Steps</label>
            <StepperInput
              value={evalSteps}
              onChange={setEvalSteps}
              step={5000}
              min={500}
              max={50000}
              presets={[1000, 5000, 10000, 25000]}
            />
          </div>
          <button
            className="btn btn-primary"
            style={{ width: '100%', marginBottom: '16px' }}
            onClick={handleEvaluate}
            disabled={!selectedModel || isEvaluating}
          >
            {isEvaluating ? <Loader2 size={13} className="spin" /> : <Play size={13} />}
            {isEvaluating ? 'Evaluating…' : 'Run Evaluation'}
          </button>
          <div className="registry-list-shell">
            <div className="registry-list-header">
              <span className="text-label">Available Models</span>
              <span className="badge">{models.length}</span>
            </div>
            <div className="registry-list">
              {models.length === 0 && (
                <p style={{ fontSize: '12px', color: 'var(--muted)', fontStyle: 'italic', padding: '12px 2px' }}>No models found</p>
              )}
              {models.length > 0 && (
                <div
                  className="group registry-compare-row"
                  onClick={() => setIsCompareModalOpen(true)}
                >
                  <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--accent)' }}>
                    <GitMerge size={12} style={{ marginRight: '6px', verticalAlign: '-2px' }} />
                    Compare All Modes...
                  </span>
                </div>
              )}
              {models.map(m => (
                <div
                  key={m}
                  className={`group registry-item ${selectedModel === m ? 'selected' : ''}`}
                  onClick={() => setSelectedModel(m)}
                >
                  <span
                    className="registry-item-name"
                    style={{
                      fontWeight: selectedModel === m ? 700 : 500,
                      color: selectedModel === m ? 'var(--text)' : 'var(--text-secondary)',
                    }}
                  >
                    {m}
                  </span>
                  <div className="registry-item-actions">
                    <button
                      className="btn btn-ghost btn-sm"
                      onClick={(e) => { e.stopPropagation(); setRenameTarget(m); setIsRenaming(true); setNewName(m); }}
                      style={{ padding: '3px' }}
                    >
                      <Edit2 size={11} />
                    </button>
                    <button
                      className="btn btn-ghost btn-sm"
                      onClick={(e) => handleRequestDelete(m, e)}
                      style={{ padding: '3px', color: 'var(--danger)' }}
                    >
                      <Trash2 size={11} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
        <section className="sidebar-section sidebar-history-section">
          <div className="card-title" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <History size={11} />
              Eval History
            </span>
            <button className="btn btn-ghost" onClick={fetchEvalHistory} style={{ padding: '3px' }}>
              <RefreshCw size={11} className={loadingEvalHistory ? 'spin' : ''} />
            </button>
          </div>
          <div style={{ overflowY: 'auto', flex: 1, marginTop: '4px' }}>
            {evalHistory.length === 0 && !loadingEvalHistory && (
              <p style={{ fontSize: '12px', color: 'var(--muted)', fontStyle: 'italic', padding: '16px 0', textAlign: 'center' }}>No history found</p>
            )}
            {evalHistory.map(h => (
              <div
                key={h.id}
                className="group"
                onClick={() => loadEvalResult(h.id)}
                style={{ padding: '8px 10px', marginBottom: '4px' }}
              >
                <div style={{ flex: 1, minWidth: 0 }}>
                  <p style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {h.id.split('_').slice(0, -2).join('_') || 'Evaluation'}
                  </p>
                  <p style={{ fontSize: '10px', color: 'var(--muted)', marginTop: '2px' }}>
                    {h.timestamp} · {h.savings?.toFixed(1)}% {getSavingsBasisLabel(h.savings_basis)}
                  </p>
                </div>
                <button
                  className="btn btn-ghost btn-sm"
                  onClick={(e) => deleteEvalResult(h.id, e)}
                  style={{ padding: '3px', color: 'var(--danger)', marginLeft: '8px' }}
                >
                  <Trash2 size={11} />
                </button>
              </div>
            ))}
          </div>
          {models.length > 0 && (
            <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px solid var(--border)' }}>
              <button
                className="btn btn-outline btn-sm"
                style={{ width: '100%', borderStyle: 'dashed' }}
                onClick={handleRequestDeleteAll}
              >
                <Trash2 size={11} />
                Clear Registry
              </button>
            </div>
          )}
        </section>
      </aside>
      <main className="main-content">
        <div className="content-area">
          <header style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-end',
            paddingBottom: '20px',
            marginBottom: '32px',
            borderBottom: '1px solid var(--border)'
          }}>
            <div>
              <h1 style={{ fontSize: '26px', letterSpacing: '-0.04em', marginBottom: '3px' }}>
                {mainTab === 'analytics' ? 'Telemetry' : mainTab === 'calculator' ? 'Sustainability' : 'Global Emissions'}
              </h1>
              <p style={{ color: 'var(--muted)', fontWeight: 600, fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
                {mainTab === 'analytics' ? 'Model evaluation & performance' : mainTab === 'calculator' ? 'Resource efficiency & ROI analysis' : 'Worldwide energy & CO₂ intelligence'}
              </p>
            </div>
            <div className="tab-bar" style={{ marginBottom: 0 }}>
              <button
                className={`tab-btn ${mainTab === 'analytics' ? 'active' : ''}`}
                onClick={() => setMainTab('analytics')}
              >
                <BarChart3 size={12} style={{ display: 'inline', verticalAlign: '-2px', marginRight: '5px' }} />
                Analytics
              </button>
              <button
                className={`tab-btn ${mainTab === 'global' ? 'active' : ''}`}
                onClick={() => setMainTab('global')}
              >
                <Globe size={12} style={{ display: 'inline', verticalAlign: '-2px', marginRight: '5px' }} />
                Global
              </button>
              <button
                className={`tab-btn ${mainTab === 'calculator' ? 'active' : ''}`}
                onClick={() => setMainTab('calculator')}
              >
                <Leaf size={12} style={{ display: 'inline', verticalAlign: '-2px', marginRight: '5px' }} />
                Calculator
              </button>
            </div>
          </header>
          {mainTab === 'analytics' && (
            <>
              {(isTraining || isEvaluating) && (
                <div className="card animate-fade-in" style={{ marginBottom: '24px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                    <Loader2 size={14} className="spin" color="var(--accent)" />
                    <span className="card-title" style={{ margin: 0 }}>
                      {isTraining ? 'Training in Progress' : 'Evaluation Running'}
                    </span>
                  </div>
                  {isTraining && (
                    <div style={{ marginBottom: '12px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
                        <span className="text-label">Progress</span>
                        <span style={{ fontSize: '11px', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>{trainingProgress}%</span>
                      </div>
                      <div className="progress-track" style={{ height: '6px' }}>
                        <div className="progress-fill" style={{ width: `${trainingProgress}%`, background: 'var(--accent)' }} />
                      </div>
                    </div>
                  )}
                  <div style={{
                    fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--text-secondary)',
                    maxHeight: '80px', overflowY: 'auto', whiteSpace: 'pre-wrap', lineHeight: 1.5,
                    padding: '10px 12px', background: 'var(--surface-raised)', borderRadius: 'var(--radius)',
                    border: '1px solid var(--border)'
                  }}>
                    {isEvaluating ? (evalLog || '> Evaluation active…') : (lastLog || '> Booting compute kernels…')}
                  </div>
                </div>
              )}
              {!results && !isEvaluating && (
                <div className="card" style={{
                  display: 'flex', flexDirection: 'column', alignItems: 'center',
                  gap: '20px', padding: '80px 40px', textAlign: 'center'
                }}>
                  <div style={{
                    width: '56px', height: '56px', borderRadius: '50%',
                    background: 'var(--surface-raised)', border: '1px solid var(--border)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center'
                  }}>
                    <BarChart3 size={24} color="var(--muted)" />
                  </div>
                  <div>
                    <h2 style={{ marginBottom: '6px' }}>No Data Available</h2>
                    <p style={{ color: 'var(--muted)', fontSize: '13px', maxWidth: '360px', margin: '0 auto' }}>
                      Select a model from the registry and run an evaluation to generate performance analytics.
                    </p>
                  </div>
                  {selectedModel && (
                    <button
                      className="btn btn-primary"
                      onClick={handleEvaluate}
                      disabled={isEvaluating}
                      style={{ marginTop: '4px' }}
                    >
                      <Play size={13} />
                      Evaluate {selectedModel}
                    </button>
                  )}
                </div>
              )}
              {results && (() => {
                const b = results.metrics.baseline;
                let s = results.metrics.scari;
                let bestModelName = "SCARI";
                if (results.metrics.models && Object.keys(results.metrics.models).length > 0) {
                  const m = results.metrics.models;
                  bestModelName = Object.keys(m).reduce((best, curr) =>
                    m[curr].total_power_consumption < m[best].total_power_consumption ? curr : best
                  );
                  s = m[bestModelName];
                }
                if (!s) return null;
                const baselineLabel = normalizeBaselineLabel(b.controller_name);
                const {
                  totalSavingsPct,
                  overheadSavingsPct,
                  coolingSavingsPct,
                  pueOverheadReductionPct
                } = getComparisonStats(b, s);
                const metrics = [
                  {
                    label: 'Controllable Reduction',
                    value: `${overheadSavingsPct.toFixed(1)}%`,
                    icon: TrendingDown,
                    color: 'var(--success)',
                    desc: `Cooling + facility overhead vs ${baselineLabel}`
                  },
                  {
                    label: 'Total Facility Reduction',
                    value: `${totalSavingsPct.toFixed(1)}%`,
                    icon: Zap,
                    color: 'var(--accent)',
                    desc: `Whole-plant power · Cooling-only: ${coolingSavingsPct.toFixed(1)}%`
                  },
                  {
                    label: `Best PUE (${bestModelName})`,
                    value: s.average_pue.toFixed(3),
                    icon: Activity,
                    color: 'var(--text)',
                    desc: `${baselineLabel} PUE: ${b.average_pue.toFixed(3)} · Overhead -${pueOverheadReductionPct.toFixed(1)}%`
                  },
                  {
                    label: 'Avg Temperature',
                    value: `${s.average_temperature.toFixed(1)}°C`,
                    icon: ThermometerSun,
                    color: s.average_temperature > 55 ? 'var(--danger)' : 'var(--text)',
                    desc: `Max: ${s.max_temperature.toFixed(1)}°C`
                  },
                  {
                    label: 'Safety Violations',
                    value: s.safety_violations,
                    icon: Shield,
                    color: s.safety_violations === 0 ? 'var(--success)' : 'var(--danger)',
                    desc: s.safety_violations === 0 ? 'Operating safely' : 'Thermal limits exceeded'
                  }
                ];
                return (
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px', marginBottom: '32px' }}>
                    {metrics.map((m, i) => (
                      <div key={i} className="metric-card animate-fade-in" style={{ animationDelay: `${i * 0.06}s` }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '7px', marginBottom: '10px' }}>
                          <m.icon size={14} color={m.color} />
                          <span className="text-label">{m.label}</span>
                        </div>
                        <div className="metric-value" style={{ fontSize: '24px', color: m.color, marginBottom: '4px' }}>
                          {m.value}
                        </div>
                        <p style={{ fontSize: '11px', color: 'var(--muted)', lineHeight: 1.3 }}>{m.desc}</p>
                      </div>
                    ))}
                    <div className="metric-card animate-fade-in" style={{ gridColumn: '1 / -1', background: 'rgba(var(--accent-rgb), 0.03)', border: '1px dashed var(--border)' }}>
                      <div style={{ display: 'flex', gap: '10px', alignItems: 'flex-start' }}>
                        <AlertCircle size={14} style={{ marginTop: '2px', color: 'var(--muted)', flexShrink: 0 }} />
                        <p style={{ fontSize: '11px', color: 'var(--muted)', fontStyle: 'italic', margin: 0 }}>
                          <strong>Note on Projections:</strong> Total savings are extrapolated from the simulation snapshot. The highlighted optimisation metric isolates controllable overhead, which better reflects what SCARI can actually tune.
                        </p>
                      </div>
                    </div>
                  </div>
                );
              })()}
              {results && (
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                    <div className="card-title" style={{ margin: 0 }}>Comparative Analysis</div>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <button className="btn btn-outline btn-sm" onClick={() => setResults(null)}>
                        <RefreshCw size={12} />
                        New Analysis
                      </button>
                      <button className="btn btn-primary btn-sm" onClick={downloadAllCharts}>
                        <Download size={12} />
                        Export All
                      </button>
                    </div>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '16px' }}>
                    {results.images.map((img, i) => {
                      const label = getChartLabel(img);
                      return (
                        <div key={i} className="card-chart animate-fade-in" style={{ animationDelay: `${i * 0.05}s` }}>
                          <div className="chart-header">
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                              <div>
                                <div className="chart-title">{label.title}</div>
                                <div className="chart-desc">{label.desc}</div>
                              </div>
                              <button
                                className="btn btn-ghost btn-sm"
                                onClick={() => downloadChart(img, `scari_${label.title.toLowerCase().replace(/\s/g, '_')}.png`)}
                                title="Download chart"
                                style={{ marginLeft: '8px', flexShrink: 0 }}
                              >
                                <Download size={13} />
                              </button>
                            </div>
                          </div>
                          <img
                            src={`${API_BASE}${img}?t=${Date.now()}`}
                            alt={label.title}
                            className="chart-img"
                            draggable={false}
                          />
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
              {results?.sustainability && (
                <section className="animate-fade-in" style={{ marginTop: '40px' }}>
                  <div className="card-title">
                    <Leaf size={11} />
                    Environmental Impact
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px' }}>
                    <div className="metric-card" style={{ borderLeft: '3px solid var(--success)' }}>
                      <span className="text-label">Projected Annual Savings</span>
                      <div className="metric-value" style={{ color: 'var(--success)', fontSize: '22px', marginTop: '6px' }}>
                        €{results.sustainability.projected_yearly_savings_eur.toLocaleString()}
                      </div>
                      <p style={{ fontSize: '11px', color: 'var(--muted)', marginTop: '6px' }}>
                        At €{results.sustainability.market_data.price_eur_kwh}/kWh industrial
                      </p>
                    </div>
                    <div className="metric-card" style={{ borderLeft: '3px solid var(--accent)' }}>
                      <span className="text-label">CO₂ Offset (Yearly)</span>
                      <div className="metric-value" style={{ color: 'var(--accent)', fontSize: '22px', marginTop: '6px' }}>
                        {results.sustainability.projected_yearly_co2_kg >= 1000
                          ? `${(results.sustainability.projected_yearly_co2_kg / 1000).toFixed(1)} t`
                          : `${results.sustainability.projected_yearly_co2_kg.toLocaleString()} kg`}
                      </div>
                      <p style={{ fontSize: '11px', color: 'var(--muted)', marginTop: '6px' }}>
                        Infrastructure carbon reduction
                      </p>
                    </div>
                    <div className="metric-card" style={{ borderLeft: '3px solid var(--text-secondary)' }}>
                      <span className="text-label">Forest Equivalent</span>
                      <div className="metric-value" style={{ fontSize: '22px', marginTop: '6px' }}>
                        {results.sustainability.trees_equivalent.toLocaleString()}
                      </div>
                      <p style={{ fontSize: '11px', color: 'var(--muted)', marginTop: '6px' }}>
                        Mature trees (absorption equiv.)
                      </p>
                    </div>
                  </div>
                </section>
              )}
              {results?.metrics?.decisions && (() => {
                let decisionsList = results.metrics.decisions;
                let traceTitle = "Decision Trace";
                if (!Array.isArray(decisionsList)) {
                  let bestModel = Object.keys(decisionsList)[0];
                  if (results.metrics.models && Object.keys(results.metrics.models).length > 0) {
                    const m = results.metrics.models;
                    bestModel = Object.keys(m).reduce((best, curr) =>
                      m[curr]?.total_power_consumption < m[best]?.total_power_consumption ? curr : best
                    );
                  }
                  decisionsList = decisionsList[bestModel];
                  traceTitle = `Decision Trace (${bestModel})`;
                }
                if (!decisionsList || decisionsList.length === 0) return null;
                return (
                  <section className="animate-fade-in" style={{ marginTop: '40px' }}>
                    <div className="card-title">
                      <Activity size={11} />
                      {traceTitle}
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: '16px' }}>
                      <div className="card" style={{ maxHeight: '560px', display: 'flex', flexDirection: 'column', padding: 0, overflow: 'hidden' }}>
                        <div className="card-header" style={{ padding: '14px 16px' }}>
                          <h3 style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <History size={13} /> Steps
                          </h3>
                          <span className="badge">{decisionsList.length}</span>
                        </div>
                        <div style={{ flex: 1, overflowY: 'auto', padding: '8px' }}>
                          {decisionsList.map((d, i) => (
                            <div
                              key={i}
                              className={`decision-item ${selectedDecision?.step === d.step ? 'active' : ''}`}
                              onClick={() => setSelectedDecision(d)}
                            >
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <span style={{ fontWeight: 600, fontSize: '12px' }}>Step {d.step}</span>
                                <span style={{
                                  fontSize: '11px', fontWeight: 700, fontFamily: 'var(--font-mono)',
                                  color: d.avg_temp > 60 ? 'var(--danger)' : d.avg_temp > 50 ? 'var(--warning)' : 'var(--success)'
                                }}>
                                  {d.avg_temp.toFixed(1)}°C
                                </span>
                              </div>
                              <div style={{ marginTop: '6px' }} className="progress-track">
                                <div className="progress-fill" style={{
                                  width: `${d.confidence * 100}%`,
                                  background: selectedDecision?.step === d.step ? 'var(--accent)' : 'var(--border-strong)'
                                }} />
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                        {selectedDecision ? (
                          <>
                            <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
                              <div className="card-header" style={{ padding: '14px 16px' }}>
                                <h3 style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                  <ChevronRight size={13} /> Control Reasoning
                                </h3>
                                <span className="badge badge-accent">
                                  {(selectedDecision.confidence * 100).toFixed(0)}% conf.
                                </span>
                              </div>
                              <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                {selectedDecision.reasoning.map((r, i) => (
                                  <div key={i} style={{ display: 'flex', gap: '10px', alignItems: 'flex-start' }}>
                                    <ChevronRight size={12} color="var(--muted)" style={{ marginTop: '3px', flexShrink: 0 }} />
                                    <p style={{ fontSize: '13px', lineHeight: 1.6, color: 'var(--text-secondary)' }}>{r}</p>
                                  </div>
                                ))}
                              </div>
                            </div>
                            <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
                              <div className="card-header" style={{ padding: '14px 16px' }}>
                                <h3 style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                  <BarChart size={13} /> Input Attribution
                                </h3>
                              </div>
                              <div style={{ padding: '16px' }}>
                                <p className="text-label" style={{ marginBottom: '14px' }}>
                                  Influence on cooling decision
                                </p>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                                  {Object.entries(selectedDecision.feature_importance).map(([feature, value], i) => (
                                    <div key={i}>
                                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '5px' }}>
                                        <span style={{ color: 'var(--text-secondary)' }}>{feature}</span>
                                        <span style={{ fontWeight: 700, fontFamily: 'var(--font-mono)' }}>{(value * 100).toFixed(1)}%</span>
                                      </div>
                                      <div className="progress-track" style={{ height: '5px' }}>
                                        <div className="progress-fill" style={{
                                          width: `${Math.min(100, value * 100 * 3)}%`,
                                          background: 'var(--accent)',
                                          transition: 'width 0.4s ease'
                                        }} />
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            </div>
                          </>
                        ) : (
                          <div className="card" style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '200px' }}>
                            <p style={{ color: 'var(--muted)', fontSize: '13px' }}>Select a step to view control reasoning</p>
                          </div>
                        )}
                      </div>
                    </div>
                  </section>
                );
              })()}
            </>
          )}
          {mainTab === 'calculator' && (
            <DataCenterCalculator onToast={addToast} evalResults={results} />
          )}
          {mainTab === 'global' && (
            <GlobalEmissions />
          )}
        </div>
      </main>
      {isCompareModalOpen && (
        <div className="modal-overlay">
          <div className="modal-content animate-slide-up" style={{ width: '400px' }}>
            <div className="modal-header">
              <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <GitMerge size={16} color="var(--accent)" />
                Multi-Model Comparison
              </h3>
            </div>
            <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '8px' }}>
                Select exactly one model of each cooling type to compare their efficiency and thermal safety.
              </p>
              <div className="form-group" style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <label style={{ color: 'var(--text)', fontSize: '11px', fontWeight: 600, textTransform: 'uppercase' }}>1. Air Cooling Model</label>
                <select
                  style={{ width: '100%', padding: '8px', borderRadius: '6px', background: 'var(--surface)', color: 'var(--text)', border: '1px solid var(--border)' }}
                  value={compareSelections.air}
                  onChange={e => setCompareSelections(p => ({ ...p, air: e.target.value }))}
                >
                  <option value="">-- Select Air Model --</option>
                  {models.map(m => <option key={`air-${m}`} value={m}>{m}</option>)}
                </select>
              </div>
              <div className="form-group" style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <label style={{ color: 'var(--text)', fontSize: '11px', fontWeight: 600, textTransform: 'uppercase' }}>2. Liquid Cooling Model</label>
                <select
                  style={{ width: '100%', padding: '8px', borderRadius: '6px', background: 'var(--surface)', color: 'var(--text)', border: '1px solid var(--border)' }}
                  value={compareSelections.liquid}
                  onChange={e => setCompareSelections(p => ({ ...p, liquid: e.target.value }))}
                >
                  <option value="">-- Select Liquid Model --</option>
                  {models.map(m => <option key={`liq-${m}`} value={m}>{m}</option>)}
                </select>
              </div>
              <div className="form-group" style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <label style={{ color: 'var(--text)', fontSize: '11px', fontWeight: 600, textTransform: 'uppercase' }}>3. Hybrid Cooling Model</label>
                <select
                  style={{ width: '100%', padding: '8px', borderRadius: '6px', background: 'var(--surface)', color: 'var(--text)', border: '1px solid var(--border)' }}
                  value={compareSelections.hybrid}
                  onChange={e => setCompareSelections(p => ({ ...p, hybrid: e.target.value }))}
                >
                  <option value="">-- Select Hybrid Model --</option>
                  {models.map(m => <option key={`hyb-${m}`} value={m}>{m}</option>)}
                </select>
              </div>
            </div>
            <div className="modal-footer" style={{ borderTop: '1px solid var(--border)', padding: '16px', marginTop: '16px', display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button className="btn btn-outline" onClick={() => setIsCompareModalOpen(false)}>Cancel</button>
              <button
                className="btn btn-primary"
                onClick={handleRunComparison}
                disabled={!compareSelections.air || !compareSelections.liquid || !compareSelections.hybrid}
              >
                Start Comparison
              </button>
            </div>
          </div>
        </div>
      )}
      <div className="toast-container">
        {toasts.map(t => <Toast key={t.id} {...t} />)}
      </div>
    </div>
  );
};
export default App;
