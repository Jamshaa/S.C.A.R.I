import React, { useState, useEffect } from 'react';
import { 
  Activity, Settings, Play, BarChart3, Cpu, Thermometer, 
  Zap, ShieldCheck, ChevronRight, RefreshCw, Terminal, 
  Download, AlertCircle, CheckCircle2, Loader2, Info
} from 'lucide-react';

const API_BASE = 'http://localhost:8000';

// Simple Toast Component
const Toast = ({ message, type, onClose }) => (
  <div className={`toast animate-fade-in ${type}`}>
    {type === 'success' ? <CheckCircle2 size={20} color="var(--success)" /> : <AlertCircle size={20} color="var(--danger)" />}
    <span style={{ fontSize: '0.9rem' }}>{message}</span>
  </div>
);

const App = () => {
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState('');
  const [isTraining, setIsTraining] = useState(false);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [lastLog, setLastLog] = useState('');
  const [results, setResults] = useState(null);
  const [trainingSteps, setTrainingSteps] = useState(25000);
  const [evalSteps, setEvalSteps] = useState(5000);
  const [toasts, setToasts] = useState([]);

  useEffect(() => {
    fetchModels();
    const interval = setInterval(fetchStatus, 2000);
    return () => clearInterval(interval);
  }, []);

  const addToast = (message, type = 'success') => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 4000);
  };

  const fetchModels = async () => {
    try {
      const res = await fetch(`${API_BASE}/models`);
      const data = await res.json();
      setModels(data.models);
      if (data.models.length > 0 && !selectedModel) setSelectedModel(data.models[0]);
    } catch (e) {
      console.error('Error fetching models', e);
    }
  };

  const fetchStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/status`);
      const data = await res.json();
      setIsTraining(data.is_training);
      if (data.is_training) setLastLog(data.last_log);
    } catch (e) { }
  };

  const handleTrain = async () => {
    try {
      const res = await fetch(`${API_BASE}/train`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ timesteps: trainingSteps })
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
    addToast(`Analysing ${selectedModel}...`, 'success');
    try {
      const evalRes = await fetch(`${API_BASE}/evaluate?model_name=${selectedModel}&steps=${evalSteps}`, { method: 'POST' });
      if (!evalRes.ok) throw new Error(await evalRes.text());
      
      const res = await fetch(`${API_BASE}/results`);
      const data = await res.json();
      setResults(data);
      addToast('Evaluation complete. dashboard updated.', 'success');
    } catch (e) {
      addToast('Evaluation failed. Check API logs.', 'error');
      console.error(e);
    } finally {
      setIsEvaluating(false);
    }
  };

  return (
    <div className="app-container">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="card animate-fade-in" style={{ padding: '1.5rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ background: 'var(--accent-primary)', padding: '0.6rem', borderRadius: '12px' }}>
            <Cpu size={28} color="#1d3557" />
          </div>
          <div>
            <h1 className="title-gradient" style={{ fontSize: '1.4rem', lineHeight: 1 }}>S.C.A.R.I</h1>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '4px' }}>AI THERMAL CONTROL v2.1</p>
          </div>
        </div>

        {/* Training Panel */}
        <section className="card animate-fade-in" style={{ animationDelay: '0.1s' }}>
          <div className="card-header">
            <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', fontSize: '1.1rem' }}>
              <Settings size={18} /> New Training
            </h2>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.2rem' }}>
            <div>
              <label className="text-label">Target Timesteps</label>
              <input 
                type="number" 
                className="input-field"
                value={trainingSteps}
                onChange={(e) => setTrainingSteps(parseInt(e.target.value))}
                placeholder="e.g. 25000"
              />
              <p style={{ fontSize: '0.65rem', color: 'var(--text-secondary)', marginTop: '0.5rem', fontStyle: 'italic' }}>
                <Info size={10} style={{ verticalAlign: 'middle', marginRight: '4px' }} />
                Higher steps = better intelligence, more time.
              </p>
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
            <RefreshCw size={14} onClick={fetchModels} style={{ cursor: 'pointer', color: 'var(--text-secondary)' }} />
          </div>
          
          <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.6rem', marginBottom: '1.5rem' }}>
            {models.length === 0 && (
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', textAlign: 'center', paddingTop: '1rem' }}>No models detected</p>
            )}
            {models.map(m => (
              <div 
                key={m} 
                onClick={() => setSelectedModel(m)}
                style={{ 
                  padding: '0.9rem', 
                  borderRadius: '10px', 
                  background: selectedModel === m ? 'rgba(168, 218, 220, 0.08)' : 'rgba(255,255,255,0.02)',
                  border: `1px solid ${selectedModel === m ? 'var(--accent-primary)' : 'var(--glass-border)'}`,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  transition: 'all 0.2s'
                }}
              >
                <span style={{ fontSize: '0.85rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{m}</span>
                {selectedModel === m && <ChevronRight size={14} color="var(--accent-primary)" />}
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
        <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <h2 style={{ fontSize: '1.8rem', fontWeight: 800 }}>Production Infrastructure</h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Deep Reinforcement Learning Thermal Management Dashboard</p>
          </div>
          <div className={`status-badge ${isTraining ? 'active' : 'idle'}`}>
             <div style={{ width: 6, height: 6, borderRadius: '50%', background: 'currentColor' }} />
             {isTraining ? 'Core Training Active' : 'System Standby'}
          </div>
        </header>

        {isTraining && (
          <div className="card animate-fade-in" style={{ borderColor: 'var(--accent-primary)', background: 'rgba(168, 218, 220, 0.03)' }}>
            <h3 style={{ marginBottom: '0.75rem', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <Terminal size={16} /> Real-time Telemetry
            </h3>
            <div style={{ 
              background: '#05070a', 
              padding: '1.25rem', 
              borderRadius: '10px', 
              fontFamily: 'monospace', 
              fontSize: '0.8rem', 
              color: '#4ade80',
              border: '1px solid #1a2230',
              maxHeight: '120px',
              overflowY: 'auto'
            }}>
              {lastLog || 'Initializing compute kernels...'}
            </div>
          </div>
        )}

        {/* Metrics Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1.5rem' }}>
          {[
            { label: 'Energy Savings', value: `${results?.metrics?.scari_v2?.power_efficiency.toFixed(1) || '0.0'}%`, icon: Activity, color: 'var(--success)', delay: '0.3s' },
            { label: 'Thermal PUE', value: results?.metrics?.scari_v2?.average_pue.toFixed(3) || '1.092', icon: Zap, color: 'var(--accent-primary)', delay: '0.4s' },
            { label: 'Avg Thermal Load', value: `${results?.metrics?.scari_v2?.average_temperature.toFixed(1) || '0.0'}°C`, icon: Thermometer, color: 'var(--warning)', delay: '0.5s' },
            { 
              label: 'Infrastructure Health', 
              value: results ? (results.metrics.scari_v2.safety_violations === 0 ? 'OPTIMIZED' : 'OVERHEAT') : 'STANDBY', 
              icon: ShieldCheck, 
              color: results?.metrics?.scari_v2?.safety_violations === 0 ? 'var(--success)' : (results ? 'var(--danger)' : 'var(--text-secondary)'),
              delay: '0.6s' 
            }
          ].map((metric, i) => (
            <div key={i} className="card animate-fade-in" style={{ animationDelay: metric.delay }}>
              <p className="text-label">{metric.label}</p>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.6rem' }}>
                <span style={{ fontSize: '1.8rem', fontWeight: 800, color: metric.color === 'var(--text-secondary)' ? 'var(--text-primary)' : metric.color }}>
                  {metric.value}
                </span>
                <metric.icon size={18} color={metric.color} style={{ opacity: 0.8 }} />
              </div>
            </div>
          ))}
        </div>

        {/* Main Analytics Area */}
        <section className="card animate-fade-in" style={{ animationDelay: '0.7s', minHeight: '500px', display: 'flex', flexDirection: 'column' }}>
          <div className="card-header">
             <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', fontSize: '1.1rem' }}>
                <BarChart3 size={20} /> Advanced Thermal Analytics
             </h3>
             <div style={{ display: 'flex', gap: '0.8rem' }}>
                <button className="btn-outline" style={{ padding: '0.5rem 1rem', fontSize: '0.75rem' }}>Report Export</button>
                <button className="btn-outline" style={{ padding: '0.5rem', borderRadius: '8px' }}><Download size={14} /></button>
             </div>
          </div>
          
          <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
             {isEvaluating ? (
               <div style={{ gridColumn: 'span 2', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '5rem' }}>
                  <div className="spinner" style={{ width: '40px', height: '40px', marginBottom: '1.5rem' }}></div>
                  <h4 style={{ color: 'var(--accent-primary)' }}>Simulating Environment...</h4>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '0.5rem' }}>Running neural network policy against baseline PID controller</p>
               </div>
             ) : results?.images?.length > 0 ? (
               results.images.map((img, i) => (
                  <div key={i} className="card" style={{ background: '#05070a', padding: '0', overflow: 'hidden', border: '1px solid #1a2230' }}>
                     <img src={`${API_BASE}${img}`} alt="plot" style={{ width: '100%', height: 'auto', display: 'block' }} />
                  </div>
               ))
             ) : (
                <div style={{ gridColumn: 'span 2', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '5rem', opacity: 0.3 }}>
                   <BarChart3 size={64} style={{ marginBottom: '1.5rem' }} />
                   <h4 style={{ fontSize: '1.2rem' }}>Awaiting Analytical Input</h4>
                   <p style={{ marginTop: '0.5rem' }}>Select a model and run analysis to populate infrastructure metrics</p>
                </div>
             )}
          </div>
        </section>
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
