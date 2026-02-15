import React, { useState, useMemo } from 'react';
import {
  BarChart3, Leaf, Zap, DollarSign, Boxes, Share2,
  TrendingDown, AlertCircle, CheckCircle2, Loader2,
  Info, ChevronDown, Gauge, PieChart, TrendingUp, Cpu,
  Download, Settings, Play, RefreshCw, Server, Thermometer,
  Building2, Factory, CircleDollarSign, TreePine, ToggleLeft, ToggleRight
} from 'lucide-react';
import { API_BASE } from './config';

// Presets for quick configuration
const PRESETS = {
  small: {
    name: 'Small DC',
    icon: Server,
    description: '50-100 servers',
    values: { num_servers: 75, annual_power_kwh: 150000, baseline_pue: 1.8, optimized_pue: 1.2, topology: 'spine_leaf' }
  },
  medium: {
    name: 'Medium DC',
    icon: Building2,
    description: '500-1000 servers',
    values: { num_servers: 750, annual_power_kwh: 1500000, baseline_pue: 1.6, optimized_pue: 1.15, topology: 'spine_leaf' }
  },
  enterprise: {
    name: 'Enterprise DC',
    icon: Factory,
    description: '5000+ servers',
    values: { num_servers: 5000, annual_power_kwh: 10000000, baseline_pue: 1.5, optimized_pue: 1.08, topology: 'fat_tree' }
  }
};

const DataCenterCalculator = ({ onToast, evalResults }) => {
  const [activeTab, setActiveTab] = useState('config');
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [selectedPreset, setSelectedPreset] = useState(null);
  
  // History state
  const [history, setHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);

  // Analysis toggles - user can choose which analyses to run
  const [analysisOptions, setAnalysisOptions] = useState({
    operational: true,
    embodied: true,
    network: true,
    roi: false
  });

  // Form state
  const [formData, setFormData] = useState({
    num_servers: 500,
    topology: 'spine_leaf',
    annual_power_kwh: 1000000,
    baseline_pue: 1.67,
    optimized_pue: 1.1,
    region: 'EU'
  });

  const [roiData, setRoiData] = useState({
    investment_eur: 500000,
    annual_savings_eur: 100000
  });

  // Calculate estimated savings in real-time
  const estimatedSavings = useMemo(() => {
    const { annual_power_kwh, baseline_pue, optimized_pue } = formData;
    const baselineEnergy = annual_power_kwh * baseline_pue;
    const optimizedEnergy = annual_power_kwh * optimized_pue;
    const energySaved = baselineEnergy - optimizedEnergy;
    const costSaved = energySaved * 0.12; // avg €0.12/kWh
    const co2Saved = energySaved * 0.4; // avg 0.4 kg CO2/kWh
    return { energySaved, costSaved, co2Saved };
  }, [formData]);

  // Import values from SCARI evaluation
  const importFromEval = (evalData = evalResults) => {
    // SCARI backend returns 'sustainability' object, not 'summary'
    const sourceData = evalData.sustainability || evalData.summary; // Fallback for safety
    
    if (!evalData || !sourceData) {
      onToast?.('No evaluation results available. Run an evaluation first!', 'error');
      return;
    }
    
    // Extract PUE values from eval results (using correct backend keys)
    const avgPUE = sourceData.pue_optimized || sourceData.avg_pue || 1.1;
    const baselinePUE = sourceData.pue_baseline || sourceData.baseline_pue || 1.67;
    // MATCH DASHBOARD: Prioritize energy_savings_percent over pue_improvement_percent
    const energySavings = sourceData.energy_savings_percent || sourceData.pue_improvement_percent || 0;
    
    setFormData(prev => ({
      ...prev,
      optimized_pue: parseFloat(avgPUE.toFixed(3)),
      baseline_pue: parseFloat(baselinePUE.toFixed(2))
    }));
    
    setSelectedPreset(null);
    setShowHistory(false);
    onToast?.(`Imported from ${evalData.id || 'current'} eval: PUE ${avgPUE.toFixed(3)}, Savings ${energySavings.toFixed(1)}%`, 'success');
  };

  const fetchHistory = async () => {
    setLoadingHistory(true);
    try {
      const res = await fetch(`${API_BASE}/history`);
      if (res.ok) {
        const data = await res.json();
        setHistory(data.history || []);
        setShowHistory(true);
      }
    } catch (e) {
      console.error("Failed to fetch history:", e);
      onToast?.("Failed to load history", "error");
    } finally {
      setLoadingHistory(false);
    }
  };

  const loadHistoricalRun = async (evalId) => {
    try {
      const res = await fetch(`${API_BASE}/history/${evalId}`);
      if (res.ok) {
        const data = await res.json();
        importFromEval(data);
      }
    } catch (e) {
      onToast?.("Failed to load historical run", "error");
    }
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setSelectedPreset(null); // Clear preset when manually editing
  };

  const handleRoiChange = (field, value) => {
    setRoiData(prev => ({ ...prev, [field]: value }));
  };

  const applyPreset = (presetKey) => {
    const preset = PRESETS[presetKey];
    setFormData(prev => ({ ...prev, ...preset.values }));
    setSelectedPreset(presetKey);
    onToast?.(`Applied ${preset.name} preset`, 'success');
  };

  const toggleAnalysisOption = (option) => {
    setAnalysisOptions(prev => ({ ...prev, [option]: !prev[option] }));
  };

  const runAnalysis = async () => {
    setIsLoading(true);
    try {
      // Run comprehensive analysis
      const res = await fetch(`${API_BASE}/calculator/comprehensive`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      
      let finalResults = { ...data.data };

      // If ROI is enabled, also run ROI analysis
      if (analysisOptions.roi) {
        const roiRes = await fetch(`${API_BASE}/calculator/roi-analysis`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            num_servers: formData.num_servers,
            ...roiData
          })
        });
        if (roiRes.ok) {
          const roiResult = await roiRes.json();
          finalResults.roi = roiResult.data;
        }
      }

      // Filter results based on selected options
      if (!analysisOptions.operational) delete finalResults.operational;
      if (!analysisOptions.embodied) delete finalResults.embodied;
      if (!analysisOptions.network) delete finalResults.network;

      setResults(finalResults);
      setActiveTab('results');
      onToast?.('Analysis complete!', 'success');
    } catch (e) {
      onToast?.(`Analysis failed: ${e.message}`, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const exportResults = () => {
    if (!results) return;
    const dataStr = JSON.stringify(results, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `scari_analysis_${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    URL.revokeObjectURL(url);
    onToast?.('Results exported!', 'success');
  };

  const TabButton = ({ id, icon: Icon, label }) => (
    <button
      onClick={() => setActiveTab(id)}
      style={{
        padding: '0.75rem 1.25rem',
        background: activeTab === id ? 'var(--gradient-success)' : 'transparent',
        color: activeTab === id ? '#000' : 'var(--text-secondary)',
        border: activeTab === id ? 'none' : '1px solid var(--glass-border)',
        borderRadius: '10px',
        cursor: 'pointer',
        fontSize: '0.85rem',
        fontWeight: activeTab === id ? '700' : '500',
        transition: 'all 0.3s ease',
        display: 'flex',
        alignItems: 'center',
        gap: '0.5rem'
      }}
    >
      <Icon size={16} />
      {label}
    </button>
  );

  const MetricCard = ({ label, value, unit, icon: Icon, color, subtitle }) => (
    <div style={{
      background: `linear-gradient(135deg, ${color}15, ${color}05)`,
      border: `1px solid ${color}30`,
      borderRadius: '12px',
      padding: '1.25rem',
      display: 'flex',
      flexDirection: 'column',
      gap: '0.5rem'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <Icon size={16} color={color} />
        <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>
          {label}
        </span>
      </div>
      <p style={{ fontSize: '1.8rem', fontWeight: 800, color }}>
        {value} <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{unit}</span>
      </p>
      {subtitle && <p style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>{subtitle}</p>}
    </div>
  );

  const ProgressBar = ({ value, max, color }) => (
    <div style={{ width: '100%', height: '8px', background: 'rgba(255,255,255,0.1)', borderRadius: '4px', overflow: 'hidden' }}>
      <div style={{ 
        width: `${Math.min(100, (value / max) * 100)}%`, 
        height: '100%', 
        background: color,
        borderRadius: '4px',
        transition: 'width 0.5s ease'
      }} />
    </div>
  );

  return (
    <div className="calculator-container">
      <div className="card" style={{ padding: '2rem' }}>
        {/* Header */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '2rem',
          paddingBottom: '1.5rem',
          borderBottom: '1px solid var(--glass-border)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{ background: 'var(--gradient-success)', padding: '0.75rem', borderRadius: '12px' }}>
              <Boxes size={28} color="#000" />
            </div>
            <div>
              <h2 style={{ fontSize: '1.6rem', marginBottom: '0.25rem', fontWeight: 800 }}>
                Sustainability Calculator
              </h2>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                Datacenter carbon footprint & ROI analysis
              </p>
            </div>
          </div>
          {results && (
            <button
              onClick={exportResults}
              style={{
                background: 'transparent',
                border: '1px solid var(--glass-border)',
                borderRadius: '8px',
                padding: '0.6rem 1rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                color: 'var(--text-secondary)',
                fontSize: '0.85rem'
              }}
            >
              <Download size={16} />
              Export JSON
            </button>
          )}
        </div>

        {/* Tabs */}
        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '2rem' }}>
          <TabButton id="config" icon={Settings} label="Configuration" />
          <TabButton id="analysis" icon={Gauge} label="Analysis Options" />
          <TabButton id="results" icon={BarChart3} label="Results" />
        </div>

        {/* Real-time Estimates Banner */}
        {activeTab !== 'results' && (
          <div style={{
            background: 'linear-gradient(135deg, rgba(0, 255, 136, 0.1), rgba(0, 212, 212, 0.05))',
            border: '1px solid rgba(0, 255, 136, 0.2)',
            borderRadius: '12px',
            padding: '1rem 1.5rem',
            marginBottom: '2rem',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: '2rem'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Zap size={18} color="var(--success)" />
              <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>Live Estimate</span>
            </div>
            <div style={{ display: 'flex', gap: '2rem' }}>
              <div>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Energy Saved</span>
                <p style={{ fontWeight: 700, color: 'var(--success)' }}>{(estimatedSavings.energySaved / 1000).toFixed(0)} MWh/yr</p>
              </div>
              <div>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Cost Reduction</span>
                <p style={{ fontWeight: 700, color: 'var(--success)' }}>€{estimatedSavings.costSaved.toLocaleString(undefined, { maximumFractionDigits: 0 })}/yr</p>
              </div>
              <div>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>CO₂ Avoided</span>
                <p style={{ fontWeight: 700, color: 'var(--success)' }}>{(estimatedSavings.co2Saved / 1000).toFixed(1)} tons/yr</p>
              </div>
            </div>
          </div>
        )}

        {/* Configuration Tab */}
        {activeTab === 'config' && (
          <div>
            {/* Presets */}
            <div style={{ marginBottom: '2rem' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Play size={16} /> Quick Presets
              </h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
                {Object.entries(PRESETS).map(([key, preset]) => (
                  <button
                    key={key}
                    onClick={() => applyPreset(key)}
                    style={{
                      padding: '1.25rem',
                      background: selectedPreset === key ? 'var(--gradient-success)' : 'var(--glass-bg)',
                      border: selectedPreset === key ? 'none' : '1px solid var(--glass-border)',
                      borderRadius: '12px',
                      cursor: 'pointer',
                      textAlign: 'left',
                      transition: 'all 0.3s ease'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                      <preset.icon size={20} color={selectedPreset === key ? '#000' : 'var(--text-secondary)'} />
                      <span style={{ fontWeight: 700, color: selectedPreset === key ? '#000' : 'var(--text-primary)' }}>{preset.name}</span>
                    </div>
                    <p style={{ fontSize: '0.8rem', color: selectedPreset === key ? 'rgba(0,0,0,0.7)' : 'var(--text-secondary)' }}>{preset.description}</p>
                  </button>
                ))}
              </div>
            </div>

            {/* Import from SCARI Evaluation & History */}
            <div style={{
              marginBottom: '2rem',
              padding: '1.5rem',
              background: 'linear-gradient(135deg, rgba(0, 243, 255, 0.05), rgba(176, 36, 255, 0.05))',
              border: '1px solid var(--glass-border)',
              borderRadius: '16px',
              position: 'relative',
              overflow: 'hidden'
            }}>
              <div style={{ 
                position: 'absolute', top: 0, left: 0, width: '4px', height: '100%', 
                background: 'linear-gradient(to bottom, #00f3ff, #b024ff)' 
              }} />
              
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: showHistory ? '1.5rem' : 0 }}>
                <div>
                  <h4 style={{ fontWeight: 700, marginBottom: '0.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '1.1rem' }}>
                    <BarChart3 size={20} color="#00f3ff" />
                    Evaluation Source
                  </h4>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                    {evalResults?.sustainability 
                      ? `Latest Run: PUE ${evalResults.sustainability.pue_optimized?.toFixed(3)}, ${evalResults.sustainability.energy_savings_percent?.toFixed(1)}% savings`
                      : 'No active evaluation results loaded'}
                  </p>
                </div>
                
                <div style={{ display: 'flex', gap: '1rem' }}>
                  <button
                    onClick={fetchHistory}
                    style={{
                      padding: '0.6rem 1.2rem',
                      background: showHistory ? 'rgba(255,255,255,0.1)' : 'transparent',
                      border: '1px solid var(--glass-border)',
                      borderRadius: '8px',
                      cursor: 'pointer',
                      fontWeight: 600,
                      fontSize: '0.85rem',
                      color: 'var(--text-primary)',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                      transition: 'all 0.3s ease'
                    }}
                  >
                    <Share2 size={16} /> History
                  </button>

                  <button
                    onClick={() => importFromEval(evalResults)}
                    disabled={!evalResults?.sustainability}
                    style={{
                      padding: '0.6rem 1.2rem',
                      background: evalResults?.sustainability ? 'var(--gradient-main)' : 'rgba(255,255,255,0.05)',
                      border: 'none',
                      borderRadius: '8px',
                      cursor: evalResults?.sustainability ? 'pointer' : 'not-allowed',
                      fontWeight: 700,
                      fontSize: '0.85rem',
                      color: evalResults?.sustainability ? '#000' : 'var(--text-secondary)',
                      opacity: evalResults?.sustainability ? 1 : 0.5,
                      boxShadow: evalResults?.sustainability ? '0 0 15px rgba(0, 243, 255, 0.3)' : 'none'
                    }}
                  >
                    Import Latest
                  </button>
                </div>
              </div>

              {/* History List */}
              {showHistory && (
                <div style={{ 
                  marginTop: '1rem', 
                  borderTop: '1px solid var(--glass-border)', 
                  paddingTop: '1rem',
                  animation: 'fadeIn 0.3s ease' 
                }}>
                  <h5 style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '1rem', display: 'flex', justifyContent: 'space-between' }}>
                    <span>Select a past run to import parameters:</span>
                    {loadingHistory && <Loader2 size={16} className="spin" />}
                  </h5>
                  
                  <div style={{ display: 'grid', gap: '0.75rem', maxHeight: '300px', overflowY: 'auto', paddingRight: '0.5rem' }}>
                    {history.length === 0 && !loadingHistory ? (
                      <p style={{ fontSize: '0.85rem', fontStyle: 'italic', color: 'var(--text-secondary)' }}>No history found.</p>
                    ) : (
                      history.map((run) => (
                        <div key={run.id} style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          padding: '1rem',
                          background: 'rgba(0,0,0,0.2)',
                          border: '1px solid var(--glass-border)',
                          borderRadius: '10px',
                          transition: 'all 0.2s ease',
                          cursor: 'pointer'
                        }}
                        className="history-item"
                        onClick={() => loadHistoricalRun(run.id)}
                        >
                          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                            <div style={{ 
                              width: '32px', height: '32px', borderRadius: '8px', 
                              background: 'var(--glass-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center' 
                            }}>
                              <TrendingUp size={16} color="var(--success)" />
                            </div>
                            <div>
                              <p style={{ fontWeight: 600, fontSize: '0.9rem' }}>{run.timestamp}</p>
                              <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                                {run.steps.toLocaleString()} steps • PUE: <span style={{ color: '#fff' }}>{run.pue ? run.pue.toFixed(3) : 'N/A'}</span>
                              </p>
                            </div>
                          </div>
                          
                          <div style={{ textAlign: 'right' }}>
                            <p style={{ fontWeight: 700, color: 'var(--success)', fontSize: '0.9rem' }}>
                              {run.savings ? run.savings.toFixed(1) : '0'}% Saved
                            </p>
                            <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', textDecoration: 'underline' }}>Load Config</span>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Manual Configuration */}
            <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Settings size={16} /> Manual Configuration
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.5rem' }}>
                  Number of Servers
                </label>
                <input
                  type="number"
                  value={formData.num_servers}
                  onChange={(e) => handleInputChange('num_servers', parseInt(e.target.value) || 0)}
                  className="input-field"
                />
                <p style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>Total physical servers in facility</p>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.5rem' }}>
                  Network Topology
                </label>
                <select
                  value={formData.topology}
                  onChange={(e) => handleInputChange('topology', e.target.value)}
                  className="input-field"
                >
                  <option value="fat_tree">Fat-Tree (DCN)</option>
                  <option value="clos">Clos (Folded)</option>
                  <option value="spine_leaf">Spine-Leaf</option>
                  <option value="three_tier">Traditional 3-Tier</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.5rem' }}>
                  Annual Power (kWh)
                </label>
                <input
                  type="number"
                  value={formData.annual_power_kwh}
                  onChange={(e) => handleInputChange('annual_power_kwh', parseFloat(e.target.value) || 0)}
                  className="input-field"
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.5rem' }}>
                  Region
                </label>
                <select
                  value={formData.region}
                  onChange={(e) => handleInputChange('region', e.target.value)}
                  className="input-field"
                >
                  <option value="EU">Europe (avg €0.12/kWh)</option>
                  <option value="US">USA (avg $0.10/kWh)</option>
                  <option value="ASIA">Asia (avg $0.08/kWh)</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.5rem' }}>
                  Baseline PUE (Current)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.baseline_pue}
                  onChange={(e) => handleInputChange('baseline_pue', parseFloat(e.target.value) || 1)}
                  className="input-field"
                />
                <ProgressBar value={formData.baseline_pue - 1} max={1} color="var(--danger)" />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.5rem' }}>
                  Optimized PUE (with S.C.A.R.I)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.optimized_pue}
                  onChange={(e) => handleInputChange('optimized_pue', parseFloat(e.target.value) || 1)}
                  className="input-field"
                />
                <ProgressBar value={formData.optimized_pue - 1} max={1} color="var(--success)" />
              </div>
            </div>
          </div>
        )}

        {/* Analysis Options Tab */}
        {activeTab === 'analysis' && (
          <div>
            <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '1.5rem' }}>
              Select which analyses to include:
            </h3>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {[
                { key: 'operational', icon: Zap, label: 'Operational Carbon', desc: 'Energy consumption & running emissions' },
                { key: 'embodied', icon: Leaf, label: 'Embodied Carbon', desc: 'Manufacturing & hardware emissions' },
                { key: 'network', icon: Share2, label: 'Network Topology', desc: 'Switch/router infrastructure analysis' },
                { key: 'roi', icon: CircleDollarSign, label: 'ROI Analysis', desc: 'Financial return projections' }
              ].map(({ key, icon: Icon, label, desc }) => (
                <div
                  key={key}
                  onClick={() => toggleAnalysisOption(key)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '1.25rem',
                    background: analysisOptions[key] ? 'rgba(0, 255, 136, 0.1)' : 'var(--glass-bg)',
                    border: `1px solid ${analysisOptions[key] ? 'var(--success)' : 'var(--glass-border)'}`,
                    borderRadius: '12px',
                    cursor: 'pointer',
                    transition: 'all 0.3s ease'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <Icon size={22} color={analysisOptions[key] ? 'var(--success)' : 'var(--text-secondary)'} />
                    <div>
                      <p style={{ fontWeight: 600, marginBottom: '0.25rem' }}>{label}</p>
                      <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{desc}</p>
                    </div>
                  </div>
                  {analysisOptions[key] ? (
                    <ToggleRight size={28} color="var(--success)" />
                  ) : (
                    <ToggleLeft size={28} color="var(--text-secondary)" />
                  )}
                </div>
              ))}
            </div>

            {/* ROI specific inputs */}
            {analysisOptions.roi && (
              <div style={{ marginTop: '2rem', padding: '1.5rem', background: 'var(--glass-bg)', borderRadius: '12px', border: '1px solid var(--glass-border)' }}>
                <h4 style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <DollarSign size={18} /> ROI Parameters
                </h4>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.5rem' }}>
                      Investment Required (€)
                    </label>
                    <input
                      type="number"
                      value={roiData.investment_eur}
                      onChange={(e) => handleRoiChange('investment_eur', parseFloat(e.target.value) || 0)}
                      className="input-field"
                    />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.5rem' }}>
                      Expected Annual Savings (€)
                    </label>
                    <input
                      type="number"
                      value={roiData.annual_savings_eur}
                      onChange={(e) => handleRoiChange('annual_savings_eur', parseFloat(e.target.value) || 0)}
                      className="input-field"
                    />
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Results Tab */}
        {activeTab === 'results' && (
          <div>
            {!results ? (
              <div style={{ textAlign: 'center', padding: '4rem 2rem' }}>
                <BarChart3 size={48} color="var(--text-secondary)" style={{ marginBottom: '1rem' }} />
                <h3 style={{ marginBottom: '0.5rem' }}>No Results Yet</h3>
                <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>Configure your datacenter and run an analysis</p>
                <button
                  onClick={() => setActiveTab('config')}
                  style={{
                    background: 'var(--gradient-success)',
                    border: 'none',
                    borderRadius: '8px',
                    padding: '0.75rem 1.5rem',
                    cursor: 'pointer',
                    fontWeight: 600,
                    color: '#000'
                  }}
                >
                  Go to Configuration
                </button>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
                {/* Summary Cards */}
                {results.summary && (
                  <div>
                    <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <PieChart size={16} /> Summary
                    </h3>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem' }}>
                      <MetricCard label="DC Size" value={results.summary.datacenter_size} unit="" icon={Server} color="#00f3ff" />
                      <MetricCard label="Total Switches" value={results.summary.total_switches} unit="" icon={Share2} color="#00ff88" />
                      <MetricCard label="Annual Carbon" value={(results.summary.total_annual_carbon_kg / 1000).toFixed(1)} unit="tons CO₂" icon={Leaf} color="#ff9500" />
                      {results.summary.breakeven_years && (
                        <MetricCard label="Break-even" value={results.summary.breakeven_years} unit="years" icon={TrendingUp} color="#00d4aa" />
                      )}
                    </div>
                  </div>
                )}

                {/* Operational Results */}
                {results.operational && (
                  <div className="card" style={{ padding: '1.5rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
                      <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <Zap size={20} color="var(--success)" /> Operational Carbon
                      </h3>
                      <span className="badge" style={{ background: 'rgba(0, 255, 136, 0.2)', color: 'var(--success)' }}>ENERGY</span>
                    </div>
                    {results.operational.improvements && (
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
                        <MetricCard
                          label="CO₂ Reduction"
                          value={results.operational.improvements.co2_reduction_kg?.toLocaleString() || 'N/A'}
                          unit="kg/yr"
                          icon={TrendingDown}
                          color="#00ff88"
                        />
                        <MetricCard
                          label="Cost Savings"
                          value={`€${results.operational.improvements.cost_savings_eur?.toLocaleString() || 'N/A'}`}
                          unit="/yr"
                          icon={DollarSign}
                          color="#4CAF50"
                        />
                        <MetricCard
                          label="Break-Even"
                          value={results.operational.improvements.breakeven_years === null ? '∞' : results.operational.improvements.breakeven_years}
                          unit="years"
                          icon={TrendingUp}
                          color="#00d4aa"
                        />
                      </div>
                    )}
                  </div>
                )}

                {/* Embodied Results */}
                {results.embodied && (
                  <div className="card" style={{ padding: '1.5rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
                      <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <Leaf size={20} color="#ff9500" /> Embodied Carbon
                      </h3>
                      <span className="badge" style={{ background: 'rgba(255, 149, 0, 0.2)', color: '#ff9500' }}>MANUFACTURING</span>
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
                      <MetricCard
                        label="Total Embodied"
                        value={(results.embodied.total_embodied_co2_kg / 1000).toFixed(1)}
                        unit="tons CO₂"
                        icon={Factory}
                        color="#ff9500"
                        subtitle="One-time manufacturing emissions"
                      />
                      <MetricCard
                        label="Annual Amortized"
                        value={results.embodied.annual_amortized_co2_kg?.toLocaleString() || 'N/A'}
                        unit="kg/yr"
                        icon={Thermometer}
                        color="#ff6b00"
                        subtitle="Spread over equipment lifespan"
                      />
                    </div>
                  </div>
                )}

                {/* Network Results */}
                {results.network && (
                  <div className="card" style={{ padding: '1.5rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
                      <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <Share2 size={20} color="#00f3ff" /> Network Topology
                      </h3>
                      <span className="badge" style={{ background: 'rgba(0, 243, 255, 0.2)', color: '#00f3ff' }}>INFRASTRUCTURE</span>
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem' }}>
                      <MetricCard label="Total Switches" value={results.network.total_switches} unit="" icon={Server} color="#00f3ff" />
                      <MetricCard label="Spine" value={results.network.spine_switches || 0} unit="" icon={Share2} color="#00d4d4" />
                      <MetricCard label="Leaf" value={results.network.leaf_switches || 0} unit="" icon={Share2} color="#00aaaa" />
                      <MetricCard label="Network CO₂" value={(results.network.network_co2_kg / 1000).toFixed(2)} unit="tons" icon={Leaf} color="#00ff88" />
                    </div>
                  </div>
                )}

                {/* ROI Results */}
                {results.roi && (
                  <div className="card" style={{ padding: '1.5rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
                      <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <DollarSign size={20} color="#00ff88" /> ROI Analysis
                      </h3>
                      <span className="badge" style={{ background: 'rgba(0, 255, 136, 0.2)', color: '#00ff88' }}>FINANCIAL</span>
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
                      <MetricCard
                        label="Annual ROI"
                        value={`${results.roi.roi_percent_annual?.toFixed(1) || 'N/A'}%`}
                        unit=""
                        icon={TrendingUp}
                        color="#00ff88"
                      />
                      <MetricCard
                        label="Payback Period"
                        value={results.roi.payback_period_years === null ? '∞' : results.roi.payback_period_years?.toFixed(1)}
                        unit="years"
                        icon={RefreshCw}
                        color="#00d4aa"
                      />
                      <MetricCard
                        label="10-Year Benefit"
                        value={`€${(results.roi.ten_year_net_benefit_eur / 1000).toFixed(0)}k`}
                        unit=""
                        icon={CircleDollarSign}
                        color="#b024ff"
                      />
                    </div>
                  </div>
                )}

                {/* Environmental Impact */}
                {results.operational?.improvements?.co2_reduction_kg && (
                  <div style={{
                    background: 'linear-gradient(135deg, rgba(0, 255, 136, 0.15), rgba(0, 212, 212, 0.1))',
                    border: '1px solid rgba(0, 255, 136, 0.3)',
                    borderRadius: '16px',
                    padding: '2rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '2rem'
                  }}>
                    <TreePine size={48} color="var(--success)" />
                    <div>
                      <h3 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '0.5rem' }}>Environmental Impact</h3>
                      <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                        Your CO₂ reduction is equivalent to planting approximately{' '}
                        <span style={{ fontWeight: 700, color: 'var(--success)' }}>
                          {Math.round(results.operational.improvements.co2_reduction_kg / 21).toLocaleString()} trees
                        </span>{' '}
                        every year.
                      </p>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Run Analysis Button */}
        {activeTab !== 'results' && (
          <button
            onClick={runAnalysis}
            disabled={isLoading}
            style={{
              width: '100%',
              marginTop: '2rem',
              padding: '1rem',
              background: isLoading ? 'var(--glass-bg)' : 'var(--gradient-success)',
              color: isLoading ? 'var(--text-secondary)' : '#000',
              border: 'none',
              borderRadius: '12px',
              fontSize: '1rem',
              fontWeight: 700,
              cursor: isLoading ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.75rem',
              transition: 'all 0.3s ease'
            }}
          >
            {isLoading ? <Loader2 size={20} className="spin" /> : <Play size={20} />}
            {isLoading ? 'Running Analysis...' : 'Run Full Analysis'}
          </button>
        )}
      </div>

      <style>{`
        .calculator-container { width: 100%; }
        .spin { animation: spin 1s linear infinite; }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
        .history-item:hover {
          background: rgba(0, 243, 255, 0.1) !important;
          border-color: rgba(0, 243, 255, 0.3) !important;
          transform: translateX(5px);
        }
      `}</style>
    </div>
  );
};

export default DataCenterCalculator;
