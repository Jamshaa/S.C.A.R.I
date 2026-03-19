import React, { useState, useMemo, useEffect } from 'react';
import {
  BarChart3, Leaf, Zap, DollarSign, Share2,
  TrendingDown, AlertCircle, CheckCircle2, Loader2,
  Download, Settings, Play, RefreshCw, Server,
  Building2, Factory, TreePine, TrendingUp, CircleDollarSign,
  Lock, Unlock, Trash2, Clock
} from 'lucide-react';
import { API_BASE } from './config';
const sanitiseText = (value = '') => String(value)
  .replaceAll('â€“', '-')
  .replaceAll('Â·', '·')
  .replaceAll('â‚¬', '€')
  .replaceAll('COâ‚‚', 'CO₂')
  .replaceAll('â€”', '—')
  .replaceAll('Î”', 'Δ')
  .replaceAll('âˆž', '∞')
  .replaceAll('Â', '');
const PRESETS = {
  small: {
    name: 'Edge / Small',
    icon: Server,
    description: '50–100 servers · Edge compute',
    values: {
      num_servers: 75,
      annual_power_kwh: 1_314_000,
      baseline_pue: 1.80,
      optimized_pue: 1.30,
      topology: 'spine_leaf'
    }
  },
  medium: {
    name: 'Regional DC',
    icon: Building2,
    description: '500–1000 servers · Regional tier',
    values: {
      num_servers: 750,
      annual_power_kwh: 26_280_000,
      baseline_pue: 1.60,
      optimized_pue: 1.15,
      topology: 'spine_leaf'
    }
  },
  enterprise: {
    name: 'Enterprise DC',
    icon: Factory,
    description: '5000+ servers · Hyperscale tier',
    values: {
      num_servers: 5000,
      annual_power_kwh: 175_200_000,
      baseline_pue: 1.50,
      optimized_pue: 1.08,
      topology: 'fat_tree'
    }
  }
};
const DEFAULT_REGION_OPTION = {
  code: 'EU',
  label: 'Europe',
  price_per_kwh: 0.18,
  carbon_intensity_kg_kwh: 0.255,
  currency_code: 'EUR',
  currency_symbol: '€'
};

const formatMoney = (value, regionInfo, maximumFractionDigits = 0) => new Intl.NumberFormat(undefined, {
  style: 'currency',
  currency: regionInfo?.currency_code || DEFAULT_REGION_OPTION.currency_code,
  maximumFractionDigits
}).format(value);

const formatCompactMoney = (value, regionInfo) => {
  const abs = Math.abs(value);
  if (abs >= 1_000_000) return `${formatMoney(value / 1_000_000, regionInfo, 1)}M`;
  if (abs >= 1_000) return `${formatMoney(value / 1_000, regionInfo, 0)}k`;
  return formatMoney(value, regionInfo, 0);
};
const getOptimizationSavingsPct = (sustainability) => (
  sustainability?.optimization_savings_percent
  ?? sustainability?.non_it_overhead_savings_percent
  ?? sustainability?.energy_savings_percent
  ?? sustainability?.pue_improvement_percent
  ?? 0
);
const getOptimizationSavingsLabel = (basis) => (
  basis === 'non_it_overhead' ? 'overhead optimisation' : 'energy savings'
);
const DataCenterCalculator = ({ onToast, evalResults }) => {
  const [activeTab, setActiveTab] = useState('config');
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [selectedPreset, setSelectedPreset] = useState(null);
  const [history, setHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [isLocked, setIsLocked] = useState(false);
  const [analysisOptions, setAnalysisOptions] = useState({
    operational: true,
    embodied: true,
    network: true,
    roi: false
  });
  const [formData, setFormData] = useState({
    num_servers: 500,
    topology: 'spine_leaf',
    annual_power_kwh: 17_520_000,
    baseline_pue: 1.67,
    optimized_pue: 1.10,
    region: 'EU'
  });
  const [roiData, setRoiData] = useState({
    investment_eur: 500000,
    annual_savings_eur: 100000
  });
  const [regionOptions, setRegionOptions] = useState([DEFAULT_REGION_OPTION]);
  const activeRegionInfo = useMemo(() => (
    regionOptions.find(option => option.code === formData.region)
    || regionOptions[0]
    || DEFAULT_REGION_OPTION
  ), [formData.region, regionOptions]);
  const resultsRegionInfo = useMemo(() => {
    const regionCode = results?.summary?.region || formData.region;
    return regionOptions.find(option => option.code === regionCode) || activeRegionInfo;
  }, [results, formData.region, regionOptions, activeRegionInfo]);
  useEffect(() => {
    let isMounted = true;
    const fetchCalculatorInfo = async () => {
      try {
        const res = await fetch(`${API_BASE}/calculator/info`);
        if (!res.ok) return;
        const data = await res.json();
        if (!isMounted || !Array.isArray(data.regions) || data.regions.length === 0) return;
        setRegionOptions(data.regions);
        setFormData(prev => (
          data.regions.some(option => option.code === prev.region)
            ? prev
            : { ...prev, region: data.regions[0].code }
        ));
      } catch (error) {
        console.debug('Failed to load calculator metadata', error);
      }
    };
    fetchCalculatorInfo();
    return () => {
      isMounted = false;
    };
  }, []);
  const estimatedSavings = useMemo(() => {
    const { annual_power_kwh, baseline_pue, optimized_pue } = formData;
    const regionInfo = activeRegionInfo;
    const baselineEnergy = annual_power_kwh * baseline_pue;
    const optimizedEnergy = annual_power_kwh * optimized_pue;
    const energySavedKwh = Math.max(0, baselineEnergy - optimizedEnergy);
    const costSaved = energySavedKwh * regionInfo.price_per_kwh;
    const co2Saved  = energySavedKwh * regionInfo.carbon_intensity_kg_kwh;
    const pueReduction = ((baseline_pue - optimized_pue) / baseline_pue) * 100;
    const energySavingPct = (energySavedKwh / baselineEnergy) * 100;
    return { energySavedKwh, costSaved, co2Saved, pueReduction, energySavingPct, regionInfo };
  }, [activeRegionInfo, formData]);
  const importFromEval = (evalData = evalResults) => {
    const src = evalData?.sustainability;
    if (!evalData || !src) {
      onToast?.('No evaluation results available. Run an evaluation first.', 'error');
      return;
    }
    const avgPUE      = src.pue_optimized ?? 1.10;
    const baselinePUE = src.pue_baseline  ?? 1.67;
    const savings_pct = getOptimizationSavingsPct(src);
    const savings_label = getOptimizationSavingsLabel(src.optimization_savings_basis);
    setFormData(prev => ({
      ...prev,
      optimized_pue: parseFloat(avgPUE.toFixed(3)),
      baseline_pue:  parseFloat(baselinePUE.toFixed(2))
    }));
    setSelectedPreset(null);
    setShowHistory(false);
    setIsLocked(true);
    onToast?.(
      `Imported evaluation PUEs: ${avgPUE.toFixed(3)} optimised, ${savings_pct.toFixed(1)}% ${savings_label}. Annual IT energy and region remain manual assumptions.`,
      'success'
    );
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
    } catch {
      onToast?.('Failed to load history', 'error');
    } finally {
      setLoadingHistory(false);
    }
  };
  const loadHistoricalRun = async (evalId) => {
    try {
      const res = await fetch(`${API_BASE}/history/${evalId}`);
      if (res.ok) importFromEval(await res.json());
    } catch {
      onToast?.('Failed to load historical run', 'error');
    }
  };
  const deleteHistoricalRun = async (evalId, e) => {
    e?.stopPropagation();
    try {
      const res = await fetch(`${API_BASE}/history/${evalId}`, { method: 'DELETE' });
      if (res.ok) {
        setHistory(prev => prev.filter(h => h.id !== evalId));
        onToast?.('Evaluation deleted', 'success');
      } else {
        onToast?.('Failed to delete', 'error');
      }
    } catch {
      onToast?.('Failed to delete evaluation', 'error');
    }
  };
  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setSelectedPreset(null);
  };
  const applyPreset = (key) => {
    setFormData(prev => ({ ...prev, ...PRESETS[key].values }));
    setSelectedPreset(key);
    setIsLocked(false);
    onToast?.(`Applied ${PRESETS[key].name} preset`, 'success');
  };
  const toggleAnalysisOption = (opt) => {
    setAnalysisOptions(prev => ({ ...prev, [opt]: !prev[opt] }));
  };
  const runAnalysis = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/calculator/comprehensive`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      let final = { ...data.data };
      if (analysisOptions.roi) {
        const roiRes = await fetch(`${API_BASE}/calculator/roi-analysis`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            num_servers: formData.num_servers, 
            investment_eur: roiData.investment_eur,
            annual_savings_eur: estimatedSavings.costSaved,
            region: formData.region
          })
        });
        if (roiRes.ok) final.roi = (await roiRes.json()).data;
      }
      if (!analysisOptions.operational) delete final.operational;
      if (!analysisOptions.embodied) delete final.embodied;
      if (!analysisOptions.network) delete final.network;
      setResults(final);
      setActiveTab('results');
      onToast?.('Analysis complete', 'success');
    } catch (e) {
      onToast?.(`Analysis failed: ${e.message}`, 'error');
    } finally {
      setIsLoading(false);
    }
  };
  const exportResults = () => {
    if (!results) return;
    const blob = new Blob([JSON.stringify(results, null, 2)], { type: 'application/json' });
    const url  = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href  = url;
    link.download = `scari_analysis_${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    URL.revokeObjectURL(url);
    onToast?.('Exported', 'success');
  };
  const PUEBar = ({ value, label, isOptimized }) => {
    const normalised = Math.max(0, Math.min(1, (value - 1.0) / 1.0));
    return (
      <div style={{ marginTop: '6px', marginBottom: '14px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
          <span className="text-label">{label}</span>
          <span style={{ 
            fontSize: '12px', fontWeight: 700, fontFamily: 'var(--font-mono)', 
            color: isOptimized ? 'var(--success)' : 'var(--warning)'
          }}>
            PUE {value.toFixed(2)}
          </span>
        </div>
        <div className="progress-track" style={{ height: '5px' }}>
          <div className="progress-fill" style={{
            width: `${normalised * 100}%`,
            background: isOptimized ? 'var(--success)' : 'var(--warning)',
          }} />
        </div>
      </div>
    );
  };
  const MetricCard = ({ label, value, unit, icon: Icon, accent = false, subtitle }) => (
    <div className="metric-card">
      <div style={{ display: 'flex', alignItems: 'center', gap: '7px', marginBottom: '10px' }}>
        {Icon && <Icon size={13} color={accent ? 'var(--success)' : 'var(--muted)'} />}
        <span className="text-label">{label}</span>
      </div>
      <div className="metric-value" style={{ fontSize: '22px', color: accent ? 'var(--success)' : 'var(--text)' }}>
        {value}
        {unit && <span style={{ fontSize: '12px', fontWeight: 500, color: 'var(--muted)', marginLeft: '4px' }}>{unit}</span>}
      </div>
      {subtitle && <p style={{ fontSize: '11px', color: 'var(--muted)', marginTop: '5px', lineHeight: 1.4 }}>{subtitle}</p>}
    </div>
  );
  return (
    <div style={{ width: '100%' }}>
      <div style={{
        display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between',
        marginBottom: '28px', paddingBottom: '20px', borderBottom: '1px solid var(--border)'
      }}>
        <div>
          <h2 style={{ fontSize: '18px', fontWeight: 800, letterSpacing: '-0.02em', marginBottom: '3px' }}>
            Sustainability Calculator
          </h2>
          <p style={{ fontSize: '12px', color: 'var(--muted)' }}>
            {sanitiseText('Carbon footprint · OpEx impact · ROI projection')}
          </p>
        </div>
        {results && (
          <button className="btn btn-outline btn-sm" onClick={exportResults}>
            <Download size={12} />
            Export
          </button>
        )}
      </div>
      <div className="tab-bar">
        {[
          { id: 'config',   label: 'Configuration' },
          { id: 'analysis', label: 'Analysis Options' },
          { id: 'results',  label: 'Results' }
        ].map(tab => (
          <button
            key={tab.id}
            className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>
      {activeTab !== 'results' && (
        <div className="card" style={{
          marginBottom: '24px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '14px',
          borderLeft: '3px solid var(--success)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Zap size={14} color="var(--success)" />
            <span style={{ fontWeight: 700, fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
              Live Projection
            </span>
            <span className="badge" style={{ fontWeight: 500 }}>
              {sanitiseText(estimatedSavings.regionInfo.label)} · {sanitiseText(estimatedSavings.regionInfo.currency_symbol)}{estimatedSavings.regionInfo.price_per_kwh}/kWh
            </span>
          </div>
          <div style={{ display: 'flex', gap: '32px', flexWrap: 'wrap' }}>
            <div>
              <div className="text-label">Energy Saved</div>
              <div style={{ fontWeight: 800, color: 'var(--success)', fontSize: '20px', letterSpacing: '-0.02em', marginTop: '2px' }}>
                {estimatedSavings.energySavedKwh >= 1_000_000
                  ? `${(estimatedSavings.energySavedKwh / 1_000_000).toFixed(1)} GWh`
                  : `${(estimatedSavings.energySavedKwh / 1000).toFixed(0)} MWh`}
              </div>
            </div>
            <div>
              <div className="text-label">Cost Delta</div>
              <div style={{ fontWeight: 800, color: 'var(--success)', fontSize: '20px', letterSpacing: '-0.02em', marginTop: '2px' }}>
                {formatCompactMoney(estimatedSavings.costSaved, estimatedSavings.regionInfo)}
              </div>
            </div>
            <div>
              <div className="text-label">CO₂ Offset</div>
              <div style={{ fontWeight: 800, color: 'var(--accent)', fontSize: '20px', letterSpacing: '-0.02em', marginTop: '2px' }}>
                {estimatedSavings.co2Saved >= 1000
                  ? `${(estimatedSavings.co2Saved / 1000).toFixed(1)} t`
                  : `${estimatedSavings.co2Saved.toFixed(0)} kg`}
              </div>
            </div>
            <div>
              <div className="text-label">PUE Δ</div>
              <div style={{ fontWeight: 800, color: 'var(--accent)', fontSize: '20px', letterSpacing: '-0.02em', marginTop: '2px' }}>
                {estimatedSavings.pueReduction.toFixed(1)}%
              </div>
            </div>
          </div>
        </div>
      )}
      {activeTab === 'config' && (
        <div>
          <div className="card-title">
            <Server size={11} />
            Quick Presets
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', marginBottom: '28px' }}>
            {Object.entries(PRESETS).map(([key, preset]) => (
              <button
                key={key}
                onClick={() => applyPreset(key)}
                className={`card ${selectedPreset === key ? 'selected' : ''}`}
                style={{
                  padding: '16px',
                  background: selectedPreset === key ? 'var(--border-strong)' : 'var(--surface)',
                  border: `1px solid ${selectedPreset === key ? 'var(--border-strong)' : 'var(--border)'}`,
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'all 0.15s ease'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                  <preset.icon size={15} color={selectedPreset === key ? 'var(--text-inverse)' : 'var(--text-secondary)'} />
                  <span style={{ fontWeight: 700, fontSize: '13px', color: selectedPreset === key ? 'var(--text-inverse)' : 'var(--text)' }}>
                    {preset.name}
                  </span>
                </div>
                <p style={{ fontSize: '11px', color: selectedPreset === key ? 'var(--text-inverse)' : 'var(--muted)', opacity: 0.85, lineHeight: 1.4 }}>
                  {sanitiseText(preset.description)}
                </p>
              </button>
            ))}
          </div>
          <div className="card" style={{ marginBottom: '28px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '3px' }}>
                  {isLocked ? <Lock size={13} color="var(--accent)" /> : <Unlock size={13} color="var(--muted)" />}
                  <span style={{ fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', fontSize: '12px' }}>
                    Evaluation Import
                  </span>
                  {isLocked && <span className="badge badge-accent">PUE locked</span>}
                </div>
                <p style={{ fontSize: '12px', color: 'var(--muted)' }}>
                  {evalResults?.sustainability
                    ? `Ready: latest evaluation exposes ${getOptimizationSavingsPct(evalResults.sustainability).toFixed(1)}% ${getOptimizationSavingsLabel(evalResults.sustainability.optimization_savings_basis)}`
                    : 'No evaluation telemetry linked'}
                </p>
                <p style={{ fontSize: '11px', color: 'var(--muted)', marginTop: '6px', lineHeight: 1.5, maxWidth: '520px' }}>
                  Only baseline and optimised PUE are imported from evaluation telemetry. Server count, topology, annual IT energy and region stay as manual planning assumptions.
                </p>
              </div>
              <div style={{ display: 'flex', gap: '6px', alignItems: 'center', flexWrap: 'wrap' }}>
                <button className="btn btn-outline btn-sm" onClick={fetchHistory}>
                  {loadingHistory ? <Loader2 size={11} className="spin" /> : <Clock size={11} />}
                  History
                </button>
                <button
                  className={`btn btn-sm ${evalResults?.sustainability ? 'btn-primary' : 'btn-outline'}`}
                  onClick={() => importFromEval(evalResults)}
                  disabled={!evalResults?.sustainability}
                >
                  Import Latest PUE
                </button>
                {isLocked && (
                  <button
                    className="btn btn-outline btn-sm"
                    onClick={() => { setIsLocked(false); onToast?.('Imported PUE fields unlocked for manual editing', 'success'); }}
                    title="Unlock imported PUE fields for manual editing"
                  >
                    <Unlock size={11} />
                    Unlock PUE
                  </button>
                )}
              </div>
            </div>
            {showHistory && (
              <div style={{ marginTop: '16px', paddingTop: '16px', borderTop: '1px solid var(--border)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                  <span className="text-label">Select a historical run</span>
                  <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                    {loadingHistory && <Loader2 size={12} className="spin" color="var(--muted)" />}
                    <button className="btn btn-ghost btn-sm" onClick={() => setShowHistory(false)} style={{ padding: '3px' }}>
                      <span style={{ fontSize: '11px' }}>Close</span>
                    </button>
                  </div>
                </div>
                <div style={{ display: 'grid', gap: '6px', maxHeight: '260px', overflowY: 'auto' }}>
                  {history.length === 0 && !loadingHistory ? (
                    <p style={{ fontSize: '12px', color: 'var(--muted)', fontStyle: 'italic' }}>No history found.</p>
                  ) : (
                    history.map((run) => (
                      <div
                        key={run.id}
                        className="group"
                        onClick={() => loadHistoricalRun(run.id)}
                        style={{ padding: '10px 12px' }}
                      >
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <p style={{ fontWeight: 600, fontSize: '12px' }}>{run.timestamp}</p>
                          <p style={{ fontSize: '11px', color: 'var(--muted)', marginTop: '2px' }}>
                            {run.steps?.toLocaleString()} steps · PUE {run.pue ? run.pue.toFixed(3) : 'N/A'} · {run.model || 'SCARI'}
                          </p>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexShrink: 0 }}>
                          <span style={{ fontWeight: 700, color: 'var(--success)', fontSize: '12px' }}>
                            {run.savings ? run.savings.toFixed(1) : '0'}% {run.savings_basis === 'non_it_overhead' ? 'OH' : 'TOT'}
                          </span>
                          <button 
                            className="btn btn-ghost btn-sm" 
                            onClick={(e) => deleteHistoricalRun(run.id, e)}
                            style={{ padding: '3px', color: 'var(--danger)' }}
                            title="Delete this run"
                          >
                            <Trash2 size={11} />
                          </button>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>
          <div className="card-title">
            <Settings size={11} />
            Manual Configuration
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '20px' }}>
            <div>
              <label>Number of Servers</label>
              <input
                type="number"
                value={formData.num_servers}
                onChange={e => handleInputChange('num_servers', parseInt(e.target.value) || 0)}
              />
              <p style={{ fontSize: '11px', color: 'var(--muted)', marginTop: '-10px' }}>Physical servers in facility</p>
            </div>
            <div>
              <label>Network Topology</label>
              <select value={formData.topology} onChange={e => handleInputChange('topology', e.target.value)}>
                <option value="fat_tree">Fat-Tree (full bisection BW)</option>
                <option value="clos">Clos (3-tier folded)</option>
                <option value="spine_leaf">Spine-Leaf (2-tier)</option>
                <option value="three_tier">3-Tier Traditional</option>
              </select>
            </div>
            <div>
              <label>Annual IT Power (kWh)</label>
              <input
                type="number"
                value={formData.annual_power_kwh}
                onChange={e => handleInputChange('annual_power_kwh', parseFloat(e.target.value) || 0)}
              />
              <p style={{ fontSize: '11px', color: 'var(--muted)', marginTop: '-10px' }}>
                IT equipment load only — overhead added via PUE
              </p>
            </div>
            <div>
              <label>Region</label>
              <select value={formData.region} onChange={e => handleInputChange('region', e.target.value)}>
                {regionOptions.map((option) => (
                  <option key={option.code} value={option.code}>
                    {sanitiseText(option.label)} ({sanitiseText(option.currency_symbol)}{option.price_per_kwh}/kWh · {option.carbon_intensity_kg_kwh} kgCO₂/kWh)
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label>Baseline PUE (current facility)</label>
              <input
                type="number"
                step="0.01"
                min="1.0"
                max="3.0"
                value={formData.baseline_pue}
                onChange={e => handleInputChange('baseline_pue', parseFloat(e.target.value) || 1)}
                disabled={isLocked}
              />
              <PUEBar value={formData.baseline_pue} label="Baseline efficiency" isOptimized={false} />
            </div>
            <div>
              <label>Optimised PUE (with S.C.A.R.I)</label>
              <input
                type="number"
                step="0.01"
                min="1.0"
                max="3.0"
                value={formData.optimized_pue}
                onChange={e => handleInputChange('optimized_pue', parseFloat(e.target.value) || 1)}
                disabled={isLocked}
              />
              <PUEBar value={formData.optimized_pue} label="Optimised efficiency" isOptimized={true} />
            </div>
          </div>
        </div>
      )}
      {activeTab === 'analysis' && (
        <div>
          <div className="card-title">Select Analyses to Run</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '24px' }}>
            {[
              { key: 'operational', label: 'Operational Carbon', desc: 'Yearly energy consumption and running CO₂ emissions', icon: Zap },
              { key: 'embodied',    label: 'Embodied Carbon',    desc: 'Manufacturing, transport and end-of-life hardware emissions', icon: Factory },
              { key: 'network',     label: 'Network Topology',   desc: 'Switch/router infrastructure analysis and carbon impact', icon: Share2 },
              { key: 'roi',        label: 'ROI Analysis',       desc: 'Financial return on investment projections over 10 years', icon: DollarSign }
            ].map(({ key, label, desc, icon: ItemIcon }) => (
              <div
                key={key}
                onClick={() => toggleAnalysisOption(key)}
                className="card"
                style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  padding: '14px 16px',
                  background: analysisOptions[key] ? 'var(--border-strong)' : 'var(--surface)',
                  cursor: 'pointer',
                  transition: 'all 0.12s ease'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  {React.createElement(ItemIcon, {
                    size: 15,
                    color: analysisOptions[key] ? 'var(--text-inverse)' : 'var(--muted)'
                  })}
                  <div>
                    <p style={{ fontWeight: 600, fontSize: '13px', color: analysisOptions[key] ? 'var(--text-inverse)' : 'var(--text)' }}>
                      {label}
                    </p>
                    <p style={{ fontSize: '11px', color: analysisOptions[key] ? 'var(--text-inverse)' : 'var(--muted)', marginTop: '1px', opacity: 0.8 }}>
                      {desc}
                    </p>
                  </div>
                </div>
                {analysisOptions[key]
                  ? <CheckCircle2 size={16} color="var(--text-inverse)" />
                  : <div style={{ width: 16, height: 16, border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', flexShrink: 0 }} />
                }
              </div>
            ))}
          </div>
          {analysisOptions.roi && (
            <div className="card animate-fade-in">
              <div className="card-title">
                <DollarSign size={11} />
                ROI Parameters
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div>
                  <label>Capital Investment ({activeRegionInfo.currency_symbol})</label>
                  <input
                    type="number"
                    value={roiData.investment_eur}
                    onChange={e => setRoiData(prev => ({ ...prev, investment_eur: parseFloat(e.target.value) || 0 }))}
                  />
                </div>
                <div>
                  <label>Expected Annual Savings (Auto-calculated)</label>
                  <input
                    type="text"
                    value={formatMoney(estimatedSavings.costSaved, estimatedSavings.regionInfo, 0)}
                    disabled={true}
                    style={{ background: 'var(--surface-raised)', color: 'var(--success)', fontWeight: 'bold' }}
                  />
                  <p style={{ fontSize: '11px', color: 'var(--muted)', marginTop: '-10px' }}>
                    Derived from total facility energy delta and the selected regional electricity price.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
      {activeTab === 'results' && (
        <div>
          {!results ? (
            <div style={{ textAlign: 'center', padding: '80px 40px' }}>
              <div style={{ 
                width: '56px', height: '56px', borderRadius: '50%', 
                background: 'var(--surface-raised)', border: '1px solid var(--border)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                margin: '0 auto 16px'
              }}>
                <BarChart3 size={24} color="var(--muted)" />
              </div>
              <h3 style={{ marginBottom: '6px' }}>No Results Yet</h3>
              <p style={{ color: 'var(--muted)', fontSize: '13px', marginBottom: '20px' }}>
                Configure your datacenter and run an analysis
              </p>
              <button className="btn btn-primary" onClick={() => setActiveTab('config')}>
                Go to Configuration
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              {results.summary && (
                <div>
                  <div className="card-title">Summary</div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '14px' }}>
                    <MetricCard label="DC Size"       value={results.summary.datacenter_size}  icon={Server} />
                    <MetricCard label="Total Switches" value={results.summary.total_switches}    icon={Share2} />
                    <MetricCard
                      label="Annual Carbon"
                      value={(results.summary.total_annual_carbon_kg / 1000).toFixed(1)}
                      unit="t CO₂"
                      icon={Leaf}
                    />
                    {results.summary.breakeven_years && (
                      <MetricCard label="Break-even" value={results.summary.breakeven_years} unit="yr" icon={TrendingUp} />
                    )}
                  </div>
                </div>
              )}
              {results.operational && (
                <div className="card">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                    <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px', margin: 0 }}>
                      <Zap size={15} color="var(--success)" /> Operational Carbon
                    </h3>
                    <span className="badge badge-success">ENERGY</span>
                  </div>
                  {results.operational.improvements && (
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: '14px' }}>
                      <MetricCard
                        label="CO₂ Reduction"
                        value={(results.operational.improvements.co2_reduction_kg / 1000).toFixed(1)}
                        unit="t/yr"
                        icon={TrendingDown}
                        accent
                      />
                      <MetricCard
                        label="Cost Savings"
                        value={formatCompactMoney(results.operational.improvements.cost_savings_eur, resultsRegionInfo)}
                        unit="/yr"
                        icon={DollarSign}
                        accent
                      />
                      <MetricCard
                        label="Break-Even"
                        value={results.operational.improvements.breakeven_years === null ? '∞' : results.operational.improvements.breakeven_years}
                        unit="yr"
                        icon={TrendingUp}
                      />
                    </div>
                  )}
                </div>
              )}
              {results.embodied && (
                <div className="card">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                    <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px', margin: 0 }}>
                      <Leaf size={15} color="var(--text-secondary)" /> Embodied Carbon
                    </h3>
                    <span className="badge">MANUFACTURING</span>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px' }}>
                    <MetricCard
                      label="Total Embodied"
                      value={(results.embodied.total_embodied_co2_kg / 1000).toFixed(1)}
                      unit="t CO₂"
                      icon={Factory}
                      subtitle="One-time manufacturing emissions"
                    />
                    <MetricCard
                      label="Annual Amortised"
                      value={results.embodied.annual_amortized_co2_kg?.toLocaleString() ?? 'N/A'}
                      unit="kg/yr"
                      subtitle="Spread over equipment lifespan"
                    />
                  </div>
                </div>
              )}
              {results.network && (
                <div className="card">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                    <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px', margin: 0 }}>
                      <Share2 size={15} color="var(--accent)" /> Network Topology
                    </h3>
                    <span className="badge badge-accent">INFRASTRUCTURE</span>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '14px' }}>
                    <MetricCard label="Total Switches" value={results.network.total_switches} unit="" icon={Server} />
                    <MetricCard label="Network Carbon" value={(results.network.total_embodied_carbon_kg / 1000).toFixed(2)} unit="t CO₂" icon={Leaf} />
                    <MetricCard label="Net Power" value={`${(results.network.estimated_network_power_w / 1000).toFixed(1)}`} unit="kW" />
                  </div>
                </div>
              )}
              {results.roi && (
                <div className="card">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                    <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px', margin: 0 }}>
                      <DollarSign size={15} color="var(--success)" /> ROI Analysis
                    </h3>
                    <span className="badge badge-success">FINANCIAL</span>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: '14px' }}>
                    <MetricCard
                      label="Annual ROI"
                      value={`${results.roi.roi_percent_annual?.toFixed(1) ?? 'N/A'}%`}
                      icon={TrendingUp}
                      accent
                    />
                    <MetricCard
                      label="Payback Period"
                      value={results.roi.payback_period_years === null ? '∞' : results.roi.payback_period_years?.toFixed(1)}
                      unit="yr"
                      icon={RefreshCw}
                    />
                    <MetricCard
                      label="10-yr Net Benefit"
                      value={formatCompactMoney(results.roi.ten_year_net_benefit_eur, resultsRegionInfo)}
                      icon={CircleDollarSign}
                    />
                  </div>
                </div>
              )}
              {results.operational?.improvements?.co2_reduction_kg && (
                <div className="card" style={{
                  display: 'flex', alignItems: 'center', gap: '20px',
                  borderLeft: '3px solid var(--success)'
                }}>
                  <TreePine size={28} color="var(--success)" style={{ flexShrink: 0 }} />
                  <div>
                    <h3 style={{ marginBottom: '4px' }}>Environmental Offset</h3>
                    <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                      Carbon reduction equivalent to{' '}
                      <strong style={{ color: 'var(--success)' }}>
                        {Math.round(results.operational.improvements.co2_reduction_kg / 21).toLocaleString()} mature trees
                      </strong>{' '}
                      added to the ecosystem annually.
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
      {activeTab !== 'results' && (
        <button
          onClick={runAnalysis}
          disabled={isLoading}
          className="btn btn-primary"
          style={{ width: '100%', marginTop: '28px', height: '44px', fontSize: '13px' }}
        >
          {isLoading ? <Loader2 size={14} className="spin" /> : <Play size={14} />}
          {isLoading ? 'Computing…' : 'Execute Analysis'}
        </button>
      )}
    </div>
  );
};
export default DataCenterCalculator;
