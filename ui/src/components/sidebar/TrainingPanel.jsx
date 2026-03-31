import React from 'react';
import { Cpu, Droplets, GitMerge, Loader2, Play, Wind } from 'lucide-react';

import StepperInput from '../StepperInput';

const COOLING_OPTIONS = [
  { id: 'AIR', icon: Wind, label: 'Air', details: 'Traditional forced-air · EUR150/srv CAPEX · PUE ~1.4' },
  { id: 'LIQUID', icon: Droplets, label: 'Water', details: 'Direct liquid cooling · EUR850/srv CAPEX · PUE ~1.05' },
  { id: 'HYBRID', icon: GitMerge, label: 'Hybrid', details: 'Air + Liquid hybrid · EUR500/srv CAPEX · PUE ~1.15' },
];

const TrainingPanel = ({
  coolingMode,
  isTraining,
  lastLog,
  onCoolingModeChange,
  onTrain,
  setTrainingName,
  setTrainingSteps,
  trainingName,
  trainingProgress,
  trainingSteps,
}) => (
  <>
    <section className="sidebar-section">
      <div className="card-title">
        <Cpu size={11} />
        Training
      </div>
      <label>Run Identifier</label>
      <input
        value={trainingName}
        onChange={(event) => setTrainingName(event.target.value)}
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
        {COOLING_OPTIONS.map((mode) => (
          <button
            key={mode.id}
            className={`preset-pill ${coolingMode === mode.id ? 'active' : ''}`}
            onClick={() => onCoolingModeChange(mode.id)}
            style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '3px', padding: '8px 4px' }}
          >
            <mode.icon size={14} />
            <span style={{ fontSize: '10px', fontWeight: 600 }}>{mode.label}</span>
          </button>
        ))}
      </div>
      <div
        style={{
          fontSize: '10px',
          color: 'var(--muted)',
          padding: '6px 8px',
          background: 'var(--surface-raised)',
          borderRadius: 'var(--radius)',
          border: '1px solid var(--border)',
          marginBottom: '8px',
          lineHeight: 1.6,
        }}
      >
        {COOLING_OPTIONS.find((mode) => mode.id === coolingMode)?.details}
      </div>
      <button
        className="btn btn-primary"
        style={{ width: '100%', marginTop: '4px' }}
        onClick={onTrain}
        disabled={isTraining}
      >
        {isTraining ? <Loader2 size={13} className="spin" /> : <Play size={13} />}
        {isTraining ? 'Training...' : 'Start Training'}
      </button>
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
          <div className="progress-fill" style={{ width: `${trainingProgress}%`, background: 'var(--accent)' }} />
        </div>
        <p
          style={{
            fontSize: '11px',
            fontFamily: 'var(--font-mono)',
            color: 'var(--muted)',
            marginTop: '6px',
            lineHeight: 1.5,
            maxHeight: '40px',
            overflow: 'hidden',
          }}
        >
          {lastLog || '> Initialising...'}
        </p>
      </div>
    )}
  </>
);

export default TrainingPanel;
