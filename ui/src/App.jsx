import React, { useState, useEffect } from 'react';
import { 
  Activity, Settings, Play, BarChart3, Cpu, Thermometer, 
  Zap, ShieldCheck, ChevronRight, RefreshCw, Terminal, 
  Download, AlertCircle, CheckCircle2, Loader2, Info,
  Brain, MessageSquare, History, BarChart, Edit2, X, Sun, Moon, Trash2, Leaf,
  Boxes
} from 'lucide-react';
import DataCenterCalculator from './DataCenterCalculator';
import { API_BASE } from './config';

const fetchWithRetry = async (url, options = {}, retries = 3) => {
  for (let i = 0; i < retries; i++) {
    try {
      const res = await fetch(url, options);
      if (res.ok) return res;
      // If 4xx error (client side), do not retry
      if (res.status >= 400 && res.status < 500) throw new Error(await res.text());
      throw new Error(`Request failed: ${res.status}`); 
    } catch (e) {
      if (i === retries - 1) throw e;
      await new Promise(r => setTimeout(r, 1000 * (i + 1))); 
    }
  }
};

// Simple Toast Component
const Toast = ({ message, type }) => (
  <div className={`toast animate-fade-in ${type}`}>
    {type === 'success' ? <CheckCircle2 size={20} color="var(--success)" /> : <AlertCircle size={20} color="var(--danger)" />}
    <span style={{ fontSize: '0.9rem' }}>{message}</span>
  </div>
);

const App = () => {
  // Core Model State
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState('');
  
  // Training State
  const [isTraining, setIsTraining] = useState(false);
  const [trainingSteps, setTrainingSteps] = useState(600000);
  const [trainingName, setTrainingName] = useState('scari_thermal_safe');
  const [trainingProgress, setTrainingProgress] = useState(0);
  const [lastLog, setLastLog] = useState('');
  
  // Evaluation State
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [evalSteps, setEvalSteps] = useState(5000);
  const [evalLog, setEvalLog] = useState('');
  const [results, setResults] = useState(null);
  
  // UI State
  const [selectedDecision, setSelectedDecision] = useState(null);
  const [isRenaming, setIsRenaming] = useState(false);
  const [renameTarget, setRenameTarget] = useState('');
  const [newName, setNewName] = useState('');
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState('');
  const [toasts, setToasts] = useState([]);
  const [theme, setTheme] = useState('dark');
  const [mainTab, setMainTab] = useState('analytics');

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  const toggleTheme = () => setTheme(prev => prev === 'dark' ? 'light' : 'dark');


  useEffect(() => {
    fetchModels();
    const interval = setInterval(fetchStatus, 2000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const addToast = (message, type = 'success') => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 4000);
  };

  const fetchModels = async () => {
    try {
      const res = await fetchWithRetry(`${API_BASE}/models`);
      const data = await res.json();
      setModels(data.models);
      if (data.models.length > 0 && !selectedModel) setSelectedModel(data.models[0]);
    } catch (e) {
      console.error('Error fetching models', e);
      addToast('Failed to connect to backend', 'error');
    }
  };

  const fetchStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/status`);
      const data = await res.json();
      setIsTraining(data.is_training);
      if (data.is_training) {
        setLastLog(data.last_log);
        setTrainingProgress(data.progress || 0);
      }
      
      const evalRes = await fetch(`${API_BASE}/evaluation-status`);
      const evalData = await evalRes.json();
      setIsEvaluating(evalData.is_evaluating);
      if (evalData.is_evaluating) setEvalLog(evalData.last_log);
    } catch (e) { 
      // Silent failure for status polling
      console.debug("Status poll failed", e);
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
    addToast(`Analysing ${selectedModel}...`, 'success');
    
    try {
      const startRes = await fetch(`${API_BASE}/evaluate?model_name=${selectedModel}&steps=${evalSteps}`, { method: 'POST' });
      if (!startRes.ok) throw new Error(await startRes.text());
      
      // Polling for results
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
            addToast('Evaluation complete. Dashboard updated.', 'success');
          }
        } catch (err) {
          console.error("Polling error:", err);
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
      
      addToast('Model renamed successfully', 'success');
      setModels(prev => prev.map(m => m === renameTarget ? (newName.endsWith('.zip') ? newName : `${newName}.zip`) : m));
      if (selectedModel === renameTarget) setSelectedModel(newName.endsWith('.zip') ? newName : `${newName}.zip`);
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
    
    // DELETE ALL
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
    } 
    // DELETE SINGLE
    else {
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

  return (
    <div className="app-container">
      {/* Delete Confirmation Modal */}
      {isDeleting && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(4px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000
        }}>
          <div className="card animate-fade-in" style={{ width: '400px', padding: '2rem', border: '1px solid var(--danger)', boxShadow: '0 0 30px rgba(239, 68, 68, 0.2)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem', color: 'var(--danger)' }}>
               <AlertCircle size={32} />
               <h3 style={{ fontSize: '1.2rem', color: 'var(--text-primary)' }}>Confirm Deletion</h3>
            </div>
            
            <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '1.5rem', lineHeight: 1.5 }}>
              {deleteTarget === 'ALL' 
                ? "Are you sure you want to DELETE ALL models? This action acts on the entire repository and cannot be undone."
                : <span>Are you sure you want to delete <b style={{color: 'var(--text-primary)'}}>{deleteTarget}</b>? This action cannot be undone.</span>
              }
            </p>
            
            <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
              <button className="btn-outline" onClick={() => setIsDeleting(false)}>Cancel</button>
              <button 
                className="btn-primary" 
                style={{ background: 'var(--danger)', borderColor: 'var(--danger)' }}
                onClick={confirmDelete}
              >
                {deleteTarget === 'ALL' ? 'Delete Everything' : 'Delete Model'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Rename Modal */}
      {isRenaming && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000
        }}>
          <div className="card animate-fade-in" style={{ width: '400px', padding: '2rem', border: '1px solid var(--accent-primary)' }}>
            <h3 style={{ marginBottom: '1rem' }}>Rename Model</h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
              Renaming {renameTarget}
            </p>
            <input 
              className="input-field" 
              value={newName} 
              onChange={e => setNewName(e.target.value)}
              placeholder="New model name..."
              autoFocus
            />
            <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem', justifyContent: 'flex-end' }}>
              <button className="btn-outline" onClick={() => setIsRenaming(false)}>Cancel</button>
              <button className="btn-primary" onClick={handleRename}>Confirm Rename</button>
            </div>
          </div>
        </div>
      )}
      
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="card" style={{ padding: '1.25rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem', background: 'rgba(255,255,255,0.03)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div className="pulse" style={{ background: 'linear-gradient(135deg, var(--accent-primary), var(--accent-tertiary))', padding: '0.6rem', borderRadius: '12px', boxShadow: '0 0 20px var(--accent-glow)' }}>
              <Cpu size={24} color="#000" />
            </div>
            <div>
              <h1 className="title-gradient" style={{ fontSize: '1.5rem', lineHeight: 1 }}>S.C.A.R.I</h1>
              <p style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginTop: '4px', letterSpacing: '0.1em' }}>ENTERPRISE AI CONTROL</p>
            </div>
          </div>
          <button 
            onClick={toggleTheme} 
            className="btn-outline"
            style={{ padding: '0.5rem', border: 'none', background: 'transparent' }}
            title="Toggle Theme"
          >
            {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
          </button>
        </div>

        {/* Training Panel */}
        <section className="card animate-fade-in" style={{ animationDelay: '0.1s' }}>
          <div className="card-header">
            <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', fontSize: '1.1rem' }}>
              <Settings size={18} /> New Training
            </h2>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.2rem' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem' }}>
              <div>
                 <label className="text-label">Model Name</label>
                 <input 
                   className="input-field"
                   value={trainingName}
                   onChange={e => setTrainingName(e.target.value)}
                   placeholder="e.g. scari_v3_optimized"
                 />
              </div>

              <div>
                <label className="text-label">Target Timesteps</label>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'rgba(0,0,0,0.2)', padding: '0.4rem', borderRadius: '12px', border: '1px solid var(--glass-border)' }}>
                   <button 
                     className="btn-outline" 
                     style={{ width: '36px', height: '36px', padding: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: '8px' }}
                     onClick={() => setTrainingSteps(Math.max(1000, trainingSteps - 1000))}
                   >
                     <ChevronRight size={16} style={{ transform: 'rotate(180deg)' }} />
                   </button>
                   <input 
                     type="number" 
                     className="input-field"
                     style={{ textAlign: 'center', border: 'none', background: 'transparent', boxShadow: 'none', padding: '0', fontSize: '1rem', fontWeight: 700 }}
                     value={trainingSteps}
                     onChange={(e) => setTrainingSteps(parseInt(e.target.value))}
                     placeholder="25000"
                   />
                   <button 
                     className="btn-outline" 
                     style={{ width: '36px', height: '36px', padding: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: '8px' }}
                     onClick={() => setTrainingSteps(trainingSteps + 1000)}
                   >
                     <ChevronRight size={16} />
                   </button>
                </div>
                <p style={{ fontSize: '0.65rem', color: 'var(--text-secondary)', marginTop: '0.5rem', fontStyle: 'italic', textAlign: 'center' }}>
                  <Info size={10} style={{ verticalAlign: 'middle', marginRight: '4px' }} />
                  Higher steps = better intelligence, more time.
                </p>
              </div>
            </div>
            <button 
              className="btn-primary" 
              onClick={handleTrain} 
              disabled={isTraining}
              style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.6rem' }}
            >
              {isTraining ? <Loader2 size={18} className="spin" /> : <Play size={18} />}
              {isTraining ? 'System training...' : 'Execute Training'}
            </button>
          </div>
        </section>

        {/* Models & Evaluation Panel */}
        <section className="card animate-fade-in" style={{ animationDelay: '0.2s', flex: 1, display: 'flex', flexDirection: 'column' }}>
          <div className="card-header">
            <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', fontSize: '1.1rem' }}>
              <ShieldCheck size={18} /> Model Repository
            </h2>
            <div style={{ display: 'flex', gap: '0.8rem', alignItems: 'center' }}>
               <Trash2 
                  size={14} 
                  onClick={handleRequestDeleteAll} 
                  style={{ cursor: 'pointer', color: 'var(--danger)', opacity: 0.7 }} 
                  title="Delete All Models" 
               />
               <RefreshCw size={14} onClick={fetchModels} style={{ cursor: 'pointer', color: 'var(--text-secondary)' }} />
            </div>
          </div>
          
          <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.6rem', marginBottom: '1.5rem' }}>
            {models.length === 0 && (
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', textAlign: 'center', paddingTop: '1rem' }}>No models detected</p>
            )}
            {models.map(m => (
              <div 
                key={m} 
                className="group"
                onClick={() => setSelectedModel(m)}
                style={{ 
                  padding: '1rem', 
                  borderRadius: '12px', 
                  background: selectedModel === m ? 'linear-gradient(90deg, rgba(0, 243, 255, 0.1), transparent)' : 'transparent',
                  border: `1px solid ${selectedModel === m ? 'var(--accent-primary)' : 'transparent'}`,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  transition: 'all 0.2s',
                  position: 'relative'
                }}
              >
                <div style={{ flex: 1, overflow: 'hidden', display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
                    <div style={{ width: 6, height: 6, borderRadius: '50%', background: selectedModel === m ? 'var(--accent-primary)' : 'var(--text-muted)' }} />
                    <span style={{ fontSize: '0.9rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', display: 'block', color: selectedModel === m ? 'var(--text-primary)' : 'var(--text-secondary)' }}>{m}</span>
                </div>
                
                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                   <Edit2 
                      size={14} 
                      className="edit-icon"
                      style={{ opacity: 0.5, cursor: 'pointer', color: 'var(--text-secondary)' }}
                      onClick={(e) => { e.stopPropagation(); setRenameTarget(m); setIsRenaming(true); setNewName(m); }}
                      title="Rename"
                   />
                   <Trash2 
                      size={14}
                      className="delete-icon"
                      style={{ opacity: 0.5, cursor: 'pointer', color: 'var(--danger)' }}
                      onClick={(e) => handleRequestDelete(m, e)}
                      title="Delete"
                   />
                </div>
              </div>
            ))}
          </div>

          <div style={{ background: 'rgba(0,0,0,0.2)', padding: '1rem', borderRadius: '12px', border: '1px solid var(--glass-border)' }}>
            <label className="text-label">Eval Duration (Steps)</label>
            <input 
              type="number" 
              className="input-field"
              style={{ marginBottom: '1rem', padding: '0.5rem' }}
              value={evalSteps}
              onChange={(e) => setEvalSteps(parseInt(e.target.value))}
            />
            <button 
              className="btn-outline" 
              style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.6rem' }}
              onClick={handleEvaluate}
              disabled={isEvaluating || !selectedModel}
            >
              {isEvaluating ? <Loader2 size={18} className="spin" /> : <Activity size={18} />}
              {isEvaluating ? 'Evaluating...' : 'Run Analysis'}
            </button>
          </div>
        </section>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        {/* Header with Navigation */}
        <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '2rem', marginBottom: '2rem' }}>
          <div style={{ flex: 1 }}>
            <h2 className="title-gradient" style={{ fontSize: '2.5rem', fontWeight: 900, marginBottom: '0.5rem' }}>
              {mainTab === 'analytics' ? '🎯 Mission Control' : '🌍 Sustainability Hub'}
            </h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
               <Activity size={16} color="var(--accent-secondary)" style={{ flexShrink: 0 }} />
               {mainTab === 'analytics' ? 'AI-Powered Thermal Management & Neural Policy Intelligence' : 'Datacenter Sustainability & ROI Analytics'}
            </p>
          </div>
          
          {/* Tab Navigation */}
          <div style={{ 
            display: 'flex', 
            gap: '0.5rem', 
            background: 'var(--glass-bg-thin)', 
            padding: '0.6rem', 
            borderRadius: '14px', 
            border: '1px solid var(--glass-border)',
            backdropFilter: 'blur(10px)',
            flexShrink: 0
          }}>
            <button
              onClick={() => setMainTab('analytics')}
              style={{
                padding: '0.65rem 1.3rem',
                background: mainTab === 'analytics' ? 'var(--gradient-main)' : 'transparent',
                color: mainTab === 'analytics' ? '#000' : 'var(--text-secondary)',
                border: mainTab === 'analytics' ? 'none' : '1px solid transparent',
                borderRadius: '10px',
                cursor: 'pointer',
                fontSize: '0.9rem',
                fontWeight: mainTab === 'analytics' ? 700 : 600,
                letterSpacing: '0.03em',
                transition: 'all 0.3s ease',
                boxShadow: mainTab === 'analytics' ? '0 4px 15px var(--accent-glow)' : 'none',
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem'
              }}
            >
              <BarChart3 size={16} />
              <span>Analytics</span>
            </button>
            
            <button
              onClick={() => setMainTab('calculator')}
              style={{
                padding: '0.65rem 1.3rem',
                background: mainTab === 'calculator' ? 'var(--gradient-success)' : 'transparent',
                color: mainTab === 'calculator' ? '#000' : 'var(--text-secondary)',
                border: mainTab === 'calculator' ? 'none' : '1px solid transparent',
                borderRadius: '10px',
                cursor: 'pointer',
                fontSize: '0.9rem',
                fontWeight: mainTab === 'calculator' ? 700 : 600,
                letterSpacing: '0.03em',
                transition: 'all 0.3s ease',
                boxShadow: mainTab === 'calculator' ? '0 4px 15px rgba(0, 255, 136, 0.4)' : 'none',
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem'
              }}
            >
              <Leaf size={16} />
              <span>Calculator</span>
            </button>
          </div>
        </header>

        {mainTab === 'analytics' && (
          <>
        {(isTraining || isEvaluating) && (
          <div className="card animate-fade-in" style={{ borderColor: 'var(--accent-primary)', background: 'rgba(168, 218, 220, 0.03)', overflow: 'visible' }}>
            <h3 style={{ marginBottom: '1rem', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <Terminal size={16} /> Real-time Telemetry {isEvaluating && '(Evaluation)'}
            </h3>
            <div style={{ padding: '1rem', background: '#05070a', borderRadius: '8px', border: '1px solid #1a2230' }}>
               {isTraining && (
                 <div style={{ marginBottom: '1rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem', fontSize: '0.8rem' }}>
                       <span style={{ color: 'var(--accent-primary)' }}>Training Progress</span>
                       <span style={{ fontWeight: 700 }}>{trainingProgress}%</span>
                    </div>
                    <div style={{ width: '100%', height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px', overflow: 'hidden' }}>
                       <div style={{ width: `${trainingProgress}%`, height: '100%', background: 'linear-gradient(90deg, var(--accent-primary), var(--accent-secondary))', transition: 'width 0.5s ease-out' }} />
                    </div>
                 </div>
               )}
               <div style={{ 
                 fontFamily: 'monospace', 
                 fontSize: '0.8rem', 
                 color: '#4ade80',
                 maxHeight: '150px',
                 overflowY: 'auto',
                 whiteSpace: 'pre-wrap',
                 wordBreak: 'break-word'
               }}>
                 {isEvaluating ? (evalLog || '> Starting evaluation sequence...') : (lastLog || '> Initializing compute kernels...')}
               </div>
            </div>
          </div>
        )}

        {/* Metrics Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1.5rem' }}>
          {(() => {
            const energySavings = results ? (results.metrics.baseline.total_power_consumption - results.metrics.scari.total_power_consumption) / results.metrics.baseline.total_power_consumption : 0;
            const metricsData = [
              { 
                label: 'Energy Savings', 
                value: results ? `${(energySavings * 100).toFixed(1)}%` : '0.0%',
                icon: Activity, 
                color: 'var(--success)', 
                delay: '0.3s',
                className: energySavings > 0.1 ? "pulse" : ""
              },
              { label: 'Efficiency Score (PUE)', value: results?.metrics?.scari?.average_pue.toFixed(3) || '1.111', icon: Zap, color: 'var(--accent-primary)', delay: '0.4s', subtitle: 'Lower is better' },
              { 
                label: 'Average Temperature', 
                value: `${results?.metrics?.scari?.average_temperature.toFixed(1) || '0.0'}°C`, 
                icon: Thermometer, 
                color: results ? (results.metrics.scari.average_temperature < 50 ? 'var(--success)' : results.metrics.scari.average_temperature < 60 ? 'var(--warning)' : 'var(--danger)') : 'var(--warning)', 
                delay: '0.5s',
                subtitle: 'Target: < 60°C'
              },
              { 
                label: 'Safety Status', 
                value: results ? (results.metrics.scari.max_temperature < 63 ? 'OPTIMAL' : results.metrics.scari.max_temperature < 75 ? 'MODERATE' : 'CRITICAL') : 'STANDBY', 
                icon: ShieldCheck, 
                color: results ? (results.metrics.scari.max_temperature < 63 ? 'var(--success)' : results.metrics.scari.max_temperature < 75 ? 'var(--warning)' : 'var(--danger)') : 'var(--text-secondary)',
                delay: '0.6s',
                subtitle: results ? `${results.metrics.scari.safety_violations} overtemp events` : null
              }
            ];
            return metricsData.map((metric, i) => (
              <div key={i} className={`card animate-fade-in ${metric.className}`} style={{ animationDelay: metric.delay }}>
                <p className="text-label">{metric.label}</p>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.6rem' }}>
                  <span style={{ fontSize: '1.8rem', fontWeight: 800, color: metric.color === 'var(--text-secondary)' ? 'var(--text-primary)' : metric.color }}>
                    {metric.value}
                  </span>
                  <metric.icon size={18} color={metric.color} style={{ opacity: 0.8 }} />
                </div>
                {metric.subtitle && (
                  <p style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
                    {metric.subtitle}
                  </p>
                )}
              </div>
            ));
          })()}
        </div>

        {/* Main Analytics Area */}
        {/* Charts Section - Full Width Vertical Scroll */}
        <div style={{ marginTop: '2rem' }}>
           <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', fontSize: '1.2rem', fontWeight: 700 }}>
                 <BarChart3 size={22} color="var(--accent-primary)" /> Performance Analysis
              </h3>
              {results?.images?.length > 0 && (
                <button 
                  className="btn-outline" 
                  style={{ padding: '0.5rem 1rem', fontSize: '0.75rem' }}
                  onClick={() => {
                    results.images.forEach((img, i) => {
                      const link = document.createElement('a');
                      link.href = `${API_BASE}${img}`;
                      link.download = `scari_chart_${i+1}.png`;
                      link.click();
                    });
                  }}
                >
                  Download All Charts
                </button>
              )}
           </div>

           <div style={{ display: 'flex', flexDirection: 'column', gap: '3rem' }}>
             {isEvaluating ? (
               <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '5rem' }}>
                  <div className="spinner" style={{ width: '40px', height: '40px', marginBottom: '1.5rem' }}></div>
                  <h4 style={{ color: 'var(--accent-primary)' }}>Simulating Environment...</h4>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '0.5rem' }}>Processing {Number(evalSteps).toLocaleString()} steps of neural policy...</p>
               </div>
             ) : results?.images?.length > 0 ? (
               results.images.map((img, i) => (
                  <div key={i} className="card" style={{ background: '#05070a', padding: '0.5rem', border: '1px solid #1a2230', position: 'relative', overflow: 'hidden', maxWidth: '850px', margin: '0 auto', width: '100%' }}>
                     <img 
                        src={`${API_BASE}${img}?t=${Date.now()}`} 
                        alt="Performance Chart" 
                        style={{ width: '100%', height: 'auto', display: 'block', borderRadius: '4px' }} 
                     />
                     <button 
                       className="btn-primary"
                       style={{ position: 'absolute', top: '15px', right: '15px', padding: '0.6rem', opacity: 0.9, zIndex: 10, boxShadow: '0 4px 12px rgba(0,0,0,0.5)' }}
                       onClick={() => {
                         const link = document.createElement('a');
                         link.href = `${API_BASE}${img}`;
                         link.download = `scari_chart_${i+1}.png`;
                         link.click();
                       }}
                       title="Download This Chart"
                     >
                        <Download size={20} color="#000" />
                     </button>
                  </div>
               ))
             ) : (
                <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '5rem', opacity: 0.5 }}>
                   <BarChart3 size={64} style={{ marginBottom: '1.5rem', color: 'var(--text-secondary)' }} />
                   <h4 style={{ fontSize: '1.2rem' }}>Ready for Analysis</h4>
                   <p style={{ marginTop: '0.5rem', color: 'var(--text-secondary)' }}>Select a model and click 'Run Analysis' to generate reports</p>
                </div>
             )}
           </div>
        </div>

        {/* Sustainability & ROI Section */}
        {results?.sustainability && (
          <section className="animate-fade-in" style={{ animationDelay: '0.7s' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '1.5rem' }}>
              <Leaf size={24} color="var(--success)" />
              <h2 style={{ fontSize: '1.5rem', fontWeight: 700 }}>Sustainability & ROI Calculator</h2>
            </div>
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.5rem' }}>
              <div className="card" style={{ borderLeft: '4px solid var(--success)' }}>
                  <p className="text-label">Est. Financial Savings (Yearly)</p>
                  <span style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--success)' }}>
                    €{results.sustainability.projected_yearly_savings_eur.toLocaleString()}
                  </span>
                  <p style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
                    Based on €{results.sustainability.market_data.price_eur_kwh}/kWh industrial rate
                  </p>
              </div>
              
              <div className="card" style={{ borderLeft: '4px solid var(--accent-secondary)' }}>
                  <p className="text-label">Carbon Offset (Yearly)</p>
                  <span style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--accent-secondary)' }}>
                    {results.sustainability.projected_yearly_co2_kg.toLocaleString()} kg CO₂
                  </span>
                  <p style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
                    Reduction in infrastructure footprint
                  </p>
              </div>
              
              <div className="card" style={{ borderLeft: '4px solid #4ade80' }}>
                  <p className="text-label">Environmental Equivalent</p>
                  <span style={{ fontSize: '1.8rem', fontWeight: 800, color: '#4ade80' }}>
                    {results.sustainability.trees_equivalent.toLocaleString()} Trees
                  </span>
                  <p style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
                    Absorption equivalent of mature forest
                  </p>
              </div>
            </div>
          </section>
        )}

        {/* Explainability Section */}
        {results?.metrics?.decisions && (
          <section className="animate-fade-in" style={{ animationDelay: '0.8s', marginTop: '2rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '1.5rem' }}>
              <Brain size={24} color="var(--accent-primary)" />
              <h2 style={{ fontSize: '1.5rem', fontWeight: 700 }}>Explainable AI Dashboard</h2>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '2rem' }}>
              {/* Decision Timeline */}
              <div className="card" style={{ maxHeight: '600px', display: 'flex', flexDirection: 'column' }}>
                <div className="card-header">
                  <h3 style={{ fontSize: '1rem' }}><History size={18} /> Decision History</h3>
                </div>
                <div style={{ flex: 1, overflowY: 'auto', padding: '1rem' }}>
                  {results.metrics.decisions.map((d, i) => (
                    <div 
                      key={i} 
                      className={`decision-item ${selectedDecision?.step === d.step ? 'active' : ''}`}
                      onClick={() => setSelectedDecision(d)}
                      style={{
                        padding: '1rem',
                        borderRadius: '12px',
                        marginBottom: '0.8rem',
                        cursor: 'pointer',
                        background: selectedDecision?.step === d.step ? 'rgba(0, 243, 255, 0.1)' : 'rgba(255, 255, 255, 0.03)',
                        border: selectedDecision?.step === d.step ? '1px solid var(--accent-primary)' : '1px solid transparent',
                        transition: 'all 0.2s ease'
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontWeight: 600 }}>Step {d.step}</span>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                          <span style={{ fontSize: '0.8rem', color: d.avg_temp > 65 ? 'var(--danger)' : 'var(--success)' }}>
                            {d.avg_temp.toFixed(1)}°C
                          </span>
                        </div>
                      </div>
                      <div style={{ marginTop: '0.5rem', height: '4px', background: 'rgba(255,255,255,0.1)', borderRadius: '2px' }}>
                        <div style={{ height: '100%', width: `${d.confidence * 100}%`, background: 'var(--accent-primary)', borderRadius: '2px' }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Reasoning & Attribution */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                {selectedDecision ? (
                  <>
                    <div className="card">
                      <div className="card-header">
                        <h3 style={{ fontSize: '1rem' }}><MessageSquare size={18} /> Agent Reasoning</h3>
                        <div className="badge" style={{ background: 'rgba(0, 243, 255, 0.1)', color: 'var(--accent-primary)' }}>
                          Confidence: {(selectedDecision.confidence * 100).toFixed(0)}%
                        </div>
                      </div>
                      <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        {selectedDecision.reasoning.map((r, i) => (
                          <div key={i} style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start' }}>
                            <div style={{ padding: '0.4rem', borderRadius: '50%', background: 'rgba(255,255,255,0.05)' }}>
                              <ChevronRight size={14} />
                            </div>
                            <p style={{ fontSize: '0.95rem', lineHeight: 1.5 }}>{r}</p>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="card">
                      <div className="card-header">
                        <h3 style={{ fontSize: '1rem' }}><BarChart size={18} /> Feature Attribution</h3>
                      </div>
                      <div style={{ padding: '1.5rem' }}>
                        <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
                          Analysis of which inputs most influenced this specific cooling decision.
                        </p>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                          {Object.entries(selectedDecision.feature_importance).map(([feature, value], i) => (
                            <div key={i}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '0.4rem' }}>
                                <span>{feature}</span>
                                <span style={{ color: 'var(--accent-primary)' }}>{(value * 100).toFixed(1)}%</span>
                              </div>
                              <div style={{ height: '8px', background: 'rgba(255,255,255,0.05)', borderRadius: '4px', overflow: 'hidden' }}>
                                <div 
                                  style={{ 
                                    height: '100%', 
                                    width: `${value * 100 * 3}%`, // Scaled for visibility
                                    background: `linear-gradient(90deg, var(--accent-primary), var(--accent-secondary))`,
                                    borderRadius: '4px'
                                  }} 
                                />
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="card" style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', opacity: 0.5 }}>
                    <p>Select a decision step to view reasoning</p>
                  </div>
                )}
              </div>
            </div>
          </section>
        )}
          </>
        )}

        {mainTab === 'calculator' && (
          <DataCenterCalculator onToast={addToast} />
        )}
      </main>

      {/* Toasts */}
      <div className="toast-container">
        {toasts.map(t => (
          <Toast key={t.id} {...t} />
        ))}
      </div>

      <style dangerouslySetInnerHTML={{ __html: `
        .spin { animation: spin 1s linear infinite; }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        .success { border-left: 4px solid var(--success) !important; }
        .error { border-left: 4px solid var(--danger) !important; }
      `}} />
    </div>
  );
};

export default App;
