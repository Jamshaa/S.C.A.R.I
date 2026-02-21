import React, { useState, useEffect } from 'react';
import { 
  Activity, Play, BarChart3, 
  RefreshCw, AlertCircle, CheckCircle2, Loader2,
  History, BarChart, Edit2, X, Sun, Moon, Trash2, Leaf,
  ChevronRight, Download, Cpu, Zap, ThermometerSun,
  Shield, TrendingDown, TreePine
} from 'lucide-react';
import DataCenterCalculator from './DataCenterCalculator';
import { API_BASE } from './config';

/* ── UTILS ──────────────────────────────────────────────────── */
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

const fmt = (n, decimals = 0) => {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(decimals)}k`;
  return n.toFixed(decimals);
};

/* ── TOAST ──────────────────────────────────────────────────── */
const Toast = ({ message, type }) => (
  <div className={`toast animate-slide-up ${type}`}>
    {type === 'success'
      ? <CheckCircle2 size={15} color="var(--success)" />
      : <AlertCircle size={15} color="var(--danger)" />}
    <span>{message}</span>
  </div>
);

/* ── MAIN APP ────────────────────────────────────────────────── */
const App = () => {
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState('');
  
  const [isTraining, setIsTraining] = useState(false);
  const [trainingSteps, setTrainingSteps] = useState(600000);
  const [trainingName, setTrainingName] = useState('scari_thermal_safe');
  const [trainingProgress, setTrainingProgress] = useState(0);
  const [lastLog, setLastLog] = useState('');
  
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [evalSteps, setEvalSteps] = useState(5000);
  const [evalLog, setEvalLog] = useState('');
  const [results, setResults] = useState(null);
  
  const [selectedDecision, setSelectedDecision] = useState(null);
  const [isRenaming, setIsRenaming] = useState(false);
  const [renameTarget, setRenameTarget] = useState('');
  const [newName, setNewName] = useState('');
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState('');
  const [toasts, setToasts] = useState([]);
  const [theme, setTheme] = useState(() =>
    window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  );
  const [mainTab, setMainTab] = useState('analytics');

  const isTrainingRef = React.useRef(isTraining);
  const isEvaluatingRef = React.useRef(isEvaluating);
  
  React.useEffect(() => { isTrainingRef.current = isTraining; }, [isTraining]);
  React.useEffect(() => { isEvaluatingRef.current = isEvaluating; }, [isEvaluating]);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  const toggleTheme = () => setTheme(prev => prev === 'dark' ? 'light' : 'dark');

  useEffect(() => {
    fetchModels();
    let isMounted = true;
    const poll = async () => {
      if (!isMounted) return;
      await fetchStatus();
      if (isMounted) setTimeout(poll, 2000);
    };
    const timeout = setTimeout(poll, 2000);
    return () => {
      isMounted = false;
      clearTimeout(timeout);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const addToast = (message, type = 'success') => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 4000);
  };

  /* ── API CALLS ─────────────────────────────────────────────── */
  const fetchModels = async () => {
    try {
      const res = await fetchWithRetry(`${API_BASE}/models`);
      if (!res) return;
      const data = await res.json();
      setModels(data.models || []);
      if (data.models?.length > 0 && !selectedModel) setSelectedModel(data.models[0]);
    } catch (e) {
      console.error('Error fetching models', e);
      addToast('Failed to connect to backend', 'error');
    }
  };

  const fetchStatus = async () => {
    try {
      const res = await fetchWithRetry(`${API_BASE}/status`);
      if (!res) return;
      const data = await res.json();
      
      const wasTraining = isTrainingRef.current;
      const nowTraining = data.is_training;
      
      if (nowTraining !== wasTraining) setIsTraining(nowTraining);
      
      if (nowTraining) {
        setLastLog(data.last_log);
        setTrainingProgress(data.progress || 0);
      } else if (wasTraining && !nowTraining) {
        setTrainingProgress(100);
        addToast('Training completed. Refreshing registry…', 'success');
        setTimeout(() => {
          setTrainingProgress(0);
          setLastLog('');
          fetchModels();
        }, 1500);
      }
      
      const evalRes = await fetch(`${API_BASE}/evaluation-status`);
      const evalData = await evalRes.json();
      
      const wasEvaluating = isEvaluatingRef.current;
      const nowEvaluating = evalData.is_evaluating;
      
      if (nowEvaluating !== wasEvaluating) setIsEvaluating(nowEvaluating);
      if (nowEvaluating) setEvalLog(evalData.last_log);
    } catch (e) { 
      console.debug('Status poll failed', e);
    }
  };

  const handleTrain = async () => {
    try {
      const res = await fetch(`${API_BASE}/train`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          timesteps: trainingSteps,
          name: trainingName.trim() || 'scari_unnamed'
        })
      });
      if (!res.ok) throw new Error(await res.text());
      addToast('Training sequence initiated', 'success');
      setIsTraining(true);
    } catch (e) {
      addToast(e.message || 'Failed to start training', 'error');
    }
  };

  const handleEvaluate = async () => {
    if (!selectedModel) {
      addToast('Please select a model first', 'error');
      return;
    }
    setIsEvaluating(true);
    setResults(null);
    addToast(`Evaluating ${selectedModel}…`, 'success');
    
    try {
      const startRes = await fetch(`${API_BASE}/evaluate?model_name=${selectedModel}&steps=${evalSteps}`, { method: 'POST' });
      if (!startRes.ok) throw new Error(await startRes.text());
      
      const pollInterval = setInterval(async () => {
        try {
          const statusRes = await fetch(`${API_BASE}/evaluation-status`);
          const statusData = await statusRes.json();
          
          if (statusData.error) {
            clearInterval(pollInterval);
            setIsEvaluating(false);
            addToast(`Evaluation failed: ${statusData.error}`, 'error');
          } else if (!statusData.is_evaluating && statusData.has_result) {
            clearInterval(pollInterval);
            setIsEvaluating(false);
            
            const resultsRes = await fetch(`${API_BASE}/results`);
            const resultsData = await resultsRes.json();
            setResults(resultsData);
            if (resultsData.metrics?.decisions?.length > 0) {
              setSelectedDecision(resultsData.metrics.decisions[0]);
            }
            addToast('Evaluation complete', 'success');
          }
        } catch (err) {
          console.error('Polling error:', err);
        }
      }, 2000);

    } catch (e) {
      addToast('Evaluation failed to start.', 'error');
      console.error(e);
      setIsEvaluating(false);
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
      } catch {
        addToast('Failed to delete all models', 'error');
      }
    } else {
      try {
        const res = await fetch(`${API_BASE}/models/${deleteTarget}`, { method: 'DELETE' });
        if (!res.ok) throw new Error(await res.text());
        addToast(`Deleted ${deleteTarget}`, 'success');
        setModels(prev => prev.filter(m => m !== deleteTarget));
        if (selectedModel === deleteTarget) setSelectedModel('');
      } catch {
        addToast('Failed to delete model', 'error');
      }
    }
    setIsDeleting(false);
    setDeleteTarget('');
  };

  /* ── MODAL OVERLAY ────────────────────────────────────────── */
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

  /* ── RENDER ────────────────────────────────────────────────── */
  return (
    <div className="app-container">
      {/* Delete Modal */}
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

      {/* Rename Modal */}
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
      
      {/* ═══════════════════════════════════════════════════════
          SIDEBAR
          ═══════════════════════════════════════════════════ */}
      <aside className="sidebar">
        {/* Brand */}
        <div style={{ 
          display: 'flex', alignItems: 'center', justifyContent: 'space-between', 
          marginBottom: '28px', paddingBottom: '20px', 
          borderBottom: '1px solid var(--border)'
        }}>
          <div>
            <h1 style={{ letterSpacing: '-0.04em', fontSize: '22px' }}>S.C.A.R.I</h1>
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

        {/* Training Config */}
        <section style={{ marginBottom: '28px' }}>
          <div className="card-title">
            <Cpu size={11} />
            Training Config
          </div>
          <div>
            <label>Run Identifier</label>
            <input 
              value={trainingName}
              onChange={e => setTrainingName(e.target.value)}
              placeholder="run_01"
            />
            <label>Timesteps</label>
            <input 
              type="number" 
              value={trainingSteps}
              onChange={(e) => setTrainingSteps(parseInt(e.target.value))}
            />
            <button 
              className="btn btn-primary" 
              style={{ width: '100%' }}
              onClick={handleTrain} 
              disabled={isTraining}
            >
              {isTraining ? <Loader2 size={13} className="spin" /> : <Play size={13} />}
              {isTraining ? 'Training…' : 'Start Training'}
            </button>
          </div>
        </section>

        {/* Training progress (inline) */}
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

        {/* Model Registry */}
        <section style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
          <div className="card-title" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Activity size={11} />
              Registry
            </span>
            <button className="btn btn-ghost" onClick={fetchModels} style={{ padding: '3px' }}>
              <RefreshCw size={11} />
            </button>
          </div>

          {/* Evaluation controls */}
          <div style={{ marginBottom: '14px' }}>
            <label>Eval Steps</label>
            <input 
              type="number" 
              value={evalSteps}
              onChange={(e) => setEvalSteps(parseInt(e.target.value))}
              style={{ marginBottom: '8px' }}
            />
            <button 
              className="btn btn-primary" 
              style={{ width: '100%' }}
              onClick={handleEvaluate}
              disabled={!selectedModel || isEvaluating}
            >
              {isEvaluating ? <Loader2 size={13} className="spin" /> : <Play size={13} />}
              {isEvaluating ? 'Evaluating…' : 'Run Evaluation'}
            </button>
          </div>
          
          <div style={{ overflowY: 'auto', flex: 1 }}>
            {models.length === 0 && (
              <p style={{ fontSize: '12px', color: 'var(--muted)', fontStyle: 'italic', padding: '8px 0' }}>No models found</p>
            )}
            {models.map(m => (
              <div 
                key={m}
                className={`group ${selectedModel === m ? 'selected' : ''}`}
                onClick={() => setSelectedModel(m)}
              >
                <span style={{
                  fontSize: '12px',
                  fontWeight: selectedModel === m ? 600 : 400,
                  color: selectedModel === m ? 'var(--text)' : 'var(--text-secondary)',
                  overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'
                }}>{m}</span>
                <div style={{ display: 'flex', gap: '4px', flexShrink: 0 }}>
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

      {/* ═══════════════════════════════════════════════════════
          MAIN CONTENT
          ═══════════════════════════════════════════════════ */}
      <main className="main-content">
        {/* Header + Tab Switcher */}
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
              {mainTab === 'analytics' ? 'Telemetry' : 'Sustainability'}
            </h1>
            <p style={{ color: 'var(--muted)', fontWeight: 600, fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
              {mainTab === 'analytics' ? 'Model evaluation & performance' : 'Resource efficiency & ROI analysis'}
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
              className={`tab-btn ${mainTab === 'calculator' ? 'active' : ''}`}
              onClick={() => setMainTab('calculator')}
            >
              <Leaf size={12} style={{ display: 'inline', verticalAlign: '-2px', marginRight: '5px' }} />
              Calculator
            </button>
          </div>
        </header>

        {/* ── ANALYTICS TAB ─────────────────────────────────── */}
        {mainTab === 'analytics' && (
          <>
            {/* Active Process Log */}
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

            {/* Empty State */}
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

            {/* Metrics Grid */}
            {results && (() => {
              const b = results.metrics.baseline;
              const s = results.metrics.scari;
              const energySavings = (b.total_power_consumption - s.total_power_consumption) / b.total_power_consumption;
              
              const metrics = [
                { 
                  label: 'Power Reduction', 
                  value: `${(energySavings * 100).toFixed(1)}%`, 
                  icon: TrendingDown, 
                  color: 'var(--success)',
                  desc: 'vs baseline PID controller'
                },
                { 
                  label: 'Average PUE', 
                  value: s.average_pue.toFixed(3), 
                  icon: Zap, 
                  color: 'var(--accent)',
                  desc: `Baseline: ${b.average_pue.toFixed(3)}`
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
                  desc: s.safety_violations === 0 ? 'Operating within limits' : 'Thermal exceedances'
                }
              ];
              
              return (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '14px', marginBottom: '32px' }}>
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
                </div>
              );
            })()}

            {/* Charts */}
            {results && (
              <div>
                <div className="card-title">Comparative Analysis</div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '16px' }}>
                  {results.images.map((img, i) => (
                    <div key={i} className="card" style={{ padding: '8px', overflow: 'hidden' }}>
                      <img 
                        src={`${API_BASE}${img}?t=${Date.now()}`} 
                        alt={`Performance chart ${i + 1}`}
                        style={{ width: '100%', height: 'auto', display: 'block', borderRadius: 'var(--radius-sm)' }} 
                      />
                    </div>
                  ))}
                </div>
                
                <div style={{ marginTop: '20px', display: 'flex', gap: '10px' }}>
                  <button className="btn btn-outline" onClick={() => setResults(null)}>
                    <RefreshCw size={12} />
                    New Analysis
                  </button>
                  <button 
                    className="btn btn-primary"
                    onClick={() => {
                      results.images.forEach((img, i) => {
                        const link = document.createElement('a');
                        link.href = `${API_BASE}${img}`;
                        link.download = `scari_chart_${i + 1}.png`;
                        link.click();
                      });
                    }}
                  >
                    <Download size={12} />
                    Export Charts
                  </button>
                </div>
              </div>
            )}

            {/* Sustainability */}
            {results?.sustainability && (
              <section className="animate-fade-in" style={{ marginTop: '40px' }}>
                <div className="card-title">
                  <Leaf size={11} />
                  Environmental Impact
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '14px' }}>
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

            {/* Decision Trace */}
            {results?.metrics?.decisions && (
              <section className="animate-fade-in" style={{ marginTop: '40px' }}>
                <div className="card-title">
                  <Activity size={11} />
                  Decision Trace
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: '16px' }}>
                  {/* Timeline */}
                  <div className="card" style={{ maxHeight: '560px', display: 'flex', flexDirection: 'column', padding: 0, overflow: 'hidden' }}>
                    <div className="card-header" style={{ padding: '14px 16px' }}>
                      <h3 style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <History size={13} /> Steps
                      </h3>
                      <span className="badge">{results.metrics.decisions.length}</span>
                    </div>
                    <div style={{ flex: 1, overflowY: 'auto', padding: '8px' }}>
                      {results.metrics.decisions.map((d, i) => (
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

                  {/* Detail panel */}
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
            )}
          </>
        )}

        {/* ── CALCULATOR TAB ────────────────────────────────── */}
        {mainTab === 'calculator' && (
          <DataCenterCalculator onToast={addToast} evalResults={results} />
        )}
      </main>

      {/* Toasts */}
      <div className="toast-container">
        {toasts.map(t => <Toast key={t.id} {...t} />)}
      </div>
    </div>
  );
};

export default App;
