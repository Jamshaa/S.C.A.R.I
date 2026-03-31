import React from 'react';
import { Activity, BarChart3, Leaf, Play } from 'lucide-react';

import { formatCoolingMode, getScenarioLabel } from '../appUtils';

const WorkflowView = ({
  handleEvaluate,
  isEvaluating,
  models,
  results,
  selectedModel,
  setMainTab,
}) => (
  <section style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
    <div className="card workflow-hero">
      <div>
        <div className="card-title" style={{ marginBottom: '10px' }}>
          <Activity size={12} />
          Main TFG Flow
        </div>
        <h2 style={{ marginBottom: '8px' }}>From checkpoint selection to defendable results</h2>
        <p style={{ fontSize: '13px', color: 'var(--text-secondary)', maxWidth: '760px' }}>
          Use this flow to pick a PPO model, launch a single evaluation,
          inspect the technical outcome and finally translate it into sustainability impact.
        </p>
      </div>
      <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
        <button className="btn btn-primary" onClick={() => setMainTab('analytics')} disabled={!selectedModel && models.length === 0}>
          <BarChart3 size={13} />
          Open Evaluation
        </button>
      </div>
    </div>

    <div className="workflow-grid">
      <div className="card workflow-step-card">
        <div className="workflow-step-index">1</div>
        <div>
          <div className="text-label">Choose Model</div>
          <h3 style={{ marginTop: '8px' }}>{selectedModel || 'No model selected yet'}</h3>
          <p style={{ fontSize: '12px', color: 'var(--muted)', marginTop: '8px' }}>
            {selectedModel
              ? 'Evaluation profile will be auto-detected from model metadata when available.'
              : 'Pick a checkpoint from the registry on the left before launching validation.'}
          </p>
        </div>
      </div>
      <div className="card workflow-step-card">
        <div className="workflow-step-index">2</div>
        <div>
          <div className="text-label">Launch Validation</div>
          <h3 style={{ marginTop: '8px' }}>Single evaluation</h3>
          <p style={{ fontSize: '12px', color: 'var(--muted)', marginTop: '8px' }}>
            Run one controlled comparison against the baseline and inspect power, thermal safety and safety-override dependence.
          </p>
        </div>
      </div>
      <div className="card workflow-step-card">
        <div className="workflow-step-index">3</div>
        <div>
          <div className="text-label">Read Outcome</div>
          <h3 style={{ marginTop: '8px' }}>{results?.context?.model || 'Awaiting evaluation output'}</h3>
          <p style={{ fontSize: '12px', color: 'var(--muted)', marginTop: '8px' }}>
            {results?.context
              ? `${getScenarioLabel(results.context)} · ${formatCoolingMode(results.context.cooling_mode)} · ${results.context.steps} steps`
              : 'The evaluation view will show who won, if the run was safe and how much SCARI relied on safety override.'}
          </p>
        </div>
      </div>
      <div className="card workflow-step-card">
        <div className="workflow-step-index">4</div>
        <div>
          <div className="text-label">Project Impact</div>
          <h3 style={{ marginTop: '8px' }}>Translate to energy, CO2 and ROI</h3>
          <p style={{ fontSize: '12px', color: 'var(--muted)', marginTop: '8px' }}>
            Push the latest evaluation into the calculator to move from technical telemetry to annual savings and sustainability narrative.
          </p>
        </div>
      </div>
    </div>

    <div className="workflow-actions-grid">
      <div className="card">
        <div className="card-title">
          <BarChart3 size={12} />
          Quick Evaluation
        </div>
        <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '14px' }}>
          Compare the selected checkpoint against its baseline and inspect metrics, charts and decision trace.
        </p>
        <button className="btn btn-primary" onClick={handleEvaluate} disabled={!selectedModel || isEvaluating}>
          <Play size={13} />
          Run Evaluation
        </button>
      </div>
      <div className="card">
        <div className="card-title">
          <Leaf size={12} />
          Sustainability Impact
        </div>
        <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '14px' }}>
          Import the latest measured PUE and use it to generate annual savings, carbon and ROI narratives.
        </p>
        <button className="btn btn-outline" onClick={() => setMainTab('calculator')}>
          <Leaf size={13} />
          Open Calculator
        </button>
      </div>
    </div>
  </section>
);

export default WorkflowView;
