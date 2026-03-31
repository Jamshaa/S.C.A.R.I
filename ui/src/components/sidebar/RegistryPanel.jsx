import React from 'react';
import { Activity, Edit2, GitMerge, Loader2, Play, RefreshCw, Trash2 } from 'lucide-react';

import StepperInput from '../StepperInput';

const RegistryPanel = ({
  evalName,
  evalSteps,
  isEvaluating,
  models,
  onDeleteAll,
  onEvaluate,
  onModelDelete,
  onModelRename,
  onModelsRefresh,
  onOpenComparison,
  selectedModel,
  setEvalName,
  setEvalSteps,
  setSelectedModel,
}) => (
  <section className="sidebar-section registry-section">
    <div className="card-title" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
        <Activity size={11} />
        Registry
      </span>
      <button className="btn btn-ghost" onClick={onModelsRefresh} style={{ padding: '3px' }}>
        <RefreshCw size={11} />
      </button>
    </div>

    <div className="registry-controls">
      <label>Run Name</label>
      <input
        value={evalName}
        onChange={(event) => setEvalName(event.target.value)}
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
      onClick={onEvaluate}
      disabled={!selectedModel || isEvaluating}
    >
      {isEvaluating ? <Loader2 size={13} className="spin" /> : <Play size={13} />}
      {isEvaluating ? 'Evaluating...' : 'Run Evaluation'}
    </button>

    <div className="registry-list-shell">
      <div className="registry-list-header">
        <span className="text-label">Available Models</span>
        <span className="badge">{models.length}</span>
      </div>
      <div className="registry-list">
        {models.length === 0 && (
          <p style={{ fontSize: '12px', color: 'var(--muted)', fontStyle: 'italic', padding: '12px 2px' }}>
            No models found
          </p>
        )}
        {models.length > 0 && (
          <div
            className="group registry-compare-row"
            onClick={onOpenComparison}
          >
            <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--accent)' }}>
              <GitMerge size={12} style={{ marginRight: '6px', verticalAlign: '-2px' }} />
              Compare All Modes...
            </span>
          </div>
        )}
        {models.map((model) => (
          <div
            key={model}
            className={`group registry-item ${selectedModel === model ? 'selected' : ''}`}
            onClick={() => setSelectedModel(model)}
          >
            <span
              className="registry-item-name"
              style={{
                fontWeight: selectedModel === model ? 700 : 500,
                color: selectedModel === model ? 'var(--text)' : 'var(--text-secondary)',
              }}
            >
              {model}
            </span>
            <div className="registry-item-actions">
              <button
                className="btn btn-ghost btn-sm"
                onClick={(event) => {
                  event.stopPropagation();
                  onModelRename(model);
                }}
                style={{ padding: '3px' }}
              >
                <Edit2 size={11} />
              </button>
              <button
                className="btn btn-ghost btn-sm"
                onClick={(event) => onModelDelete(model, event)}
                style={{ padding: '3px', color: 'var(--danger)' }}
              >
                <Trash2 size={11} />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>

    {models.length > 0 && (
      <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px solid var(--border)' }}>
        <button
          className="btn btn-outline btn-sm"
          style={{ width: '100%', borderStyle: 'dashed' }}
          onClick={onDeleteAll}
        >
          <Trash2 size={11} />
          Clear Registry
        </button>
      </div>
    )}
  </section>
);

export default RegistryPanel;
