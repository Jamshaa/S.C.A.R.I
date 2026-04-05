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
          How It Works
        </div>
        <h2 style={{ marginBottom: '8px' }}>Run and Review</h2>
        <p style={{ fontSize: '13px', color: 'var(--text-secondary)', maxWidth: '760px' }}>
          Use this flow to pick a model, run one test, review the results,
          and turn them into yearly savings and impact.
        </p>
      </div>
      <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
        <button className="btn btn-primary" onClick={() => setMainTab('analytics')} disabled={!selectedModel && models.length === 0}>
          <BarChart3 size={13} />
          Open Results
        </button>
      </div>
    </div>

    <div className="workflow-grid">
      <div className="card workflow-step-card">
        <div className="workflow-step-index">1</div>
        <div>
          <div className="text-label">Pick a Model</div>
          <h3 style={{ marginTop: '8px' }}>{selectedModel || 'No model selected yet'}</h3>
          <p style={{ fontSize: '12px', color: 'var(--muted)', marginTop: '8px' }}>
            {selectedModel
              ? 'The right setup will be picked automatically from saved model data when available.'
              : 'Pick a model from the list on the left before starting a test.'}
          </p>
        </div>
      </div>
      <div className="card workflow-step-card">
        <div className="workflow-step-index">2</div>
        <div>
          <div className="text-label">Run Test</div>
          <h3 style={{ marginTop: '8px' }}>One test</h3>
          <p style={{ fontSize: '12px', color: 'var(--muted)', marginTop: '8px' }}>
            Run one comparison and check energy use, temperature and heat safety.
          </p>
        </div>
      </div>
      <div className="card workflow-step-card">
        <div className="workflow-step-index">3</div>
        <div>
          <div className="text-label">See Results</div>
          <h3 style={{ marginTop: '8px' }}>{results?.context?.model || 'Waiting for results'}</h3>
          <p style={{ fontSize: '12px', color: 'var(--muted)', marginTop: '8px' }}>
            {results?.context
              ? `${getScenarioLabel(results.context)} | ${formatCoolingMode(results.context.cooling_mode)} | ${results.context.steps} steps`
              : 'The results view will show the winner, any heat issues and the main numbers.'}
          </p>
        </div>
      </div>
      <div className="card workflow-step-card">
        <div className="workflow-step-index">4</div>
        <div>
          <div className="text-label">Estimate Impact</div>
          <h3 style={{ marginTop: '8px' }}>Turn results into savings, CO2 and ROI</h3>
          <p style={{ fontSize: '12px', color: 'var(--muted)', marginTop: '8px' }}>
            Send the latest run to the calculator to estimate yearly savings and climate impact.
          </p>
        </div>
      </div>
    </div>

    <div className="workflow-actions-grid">
      <div className="card">
        <div className="card-title">
          <BarChart3 size={12} />
          Quick Test
        </div>
        <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '14px' }}>
          Run the selected model and review the numbers, charts and decision steps.
        </p>
        <button className="btn btn-primary" onClick={handleEvaluate} disabled={!selectedModel || isEvaluating}>
          <Play size={13} />
          Run Test
        </button>
      </div>
      <div className="card">
        <div className="card-title">
          <Leaf size={12} />
          Savings Outlook
        </div>
        <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '14px' }}>
          Use the latest run to estimate yearly savings, carbon impact and ROI.
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
