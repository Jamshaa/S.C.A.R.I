import React from 'react';
import {
  Activity,
  AlertCircle,
  BarChart,
  BarChart3,
  CheckCircle2,
  ChevronRight,
  Download,
  History,
  Image,
  Leaf,
  Loader2,
  Play,
  RefreshCw,
  Shield,
  ThermometerSun,
  Zap,
} from 'lucide-react';

import { buildApiUrl } from '../apiClient';
import {
  buildEvaluationStory,
  downloadFileFromApi,
  formatConfigLabel,
  formatCoolingMode,
  getChartLabel,
  getComparisonStats,
  getOverrideDependence,
  getScenarioLabel,
  inferEvaluationConfig,
} from '../appUtils';

const AnalyticsView = ({
  addToast,
  downloadAllCharts,
  downloadChart,
  evalLog,
  evalSteps,
  handleEvaluate,
  isEvaluating,
  isTraining,
  lastLog,
  results,
  selectedDecision,
  selectedModel,
  setResults,
  setSelectedDecision,
  trainingProgress,
}) => {
  let content = null;

  if (isTraining || isEvaluating) {
    content = (
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
        <div
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '12px',
            color: 'var(--text-secondary)',
            maxHeight: '80px',
            overflowY: 'auto',
            whiteSpace: 'pre-wrap',
            lineHeight: 1.5,
            padding: '10px 12px',
            background: 'var(--surface-raised)',
            borderRadius: 'var(--radius)',
            border: '1px solid var(--border)',
          }}
        >
          {isEvaluating ? (evalLog || '> Evaluation active...') : (lastLog || '> Booting compute kernels...')}
        </div>
      </div>
    );
  }

  if (!results && !content) {
    content = (
      <div
        className="card"
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '20px',
          padding: '80px 40px',
          textAlign: 'center',
        }}
      >
        <div
          style={{
            width: '56px',
            height: '56px',
            borderRadius: '50%',
            background: 'var(--surface-raised)',
            border: '1px solid var(--border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
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
    );
  }

  if (!results) {
    return content;
  }

  const baseline = results.metrics.baseline;
  let selectedMetrics = results.metrics.scari;
  let bestModelName = 'SCARI';

  if (results.metrics.models && Object.keys(results.metrics.models).length > 0) {
    const modelMetrics = results.metrics.models;
    bestModelName = Object.keys(modelMetrics).reduce((best, current) => (
      modelMetrics[current].total_power_consumption < modelMetrics[best].total_power_consumption ? current : best
    ));
    selectedMetrics = modelMetrics[bestModelName];
  }

  if (!selectedMetrics) {
    return content;
  }

  const { totalSavingsPct } = getComparisonStats(baseline, selectedMetrics);
  const fallbackConfig = inferEvaluationConfig(bestModelName);
  const context = results.context || {
    model: bestModelName,
    config: fallbackConfig,
    cooling_mode: fallbackConfig.includes('liquid')
      ? 'LIQUID'
      : fallbackConfig.includes('hybrid')
        ? 'HYBRID'
        : 'AIR',
    baseline: results.metrics?.metadata?.baseline_controller || baseline.controller_name || 'BASELINE',
    seed: results.metrics?.metadata?.seed ?? 'N/A',
    steps: selectedMetrics.total_steps || baseline.total_steps || evalSteps,
  };

  const safetyOverrideRate = Number(selectedMetrics.safety_override_rate_percent || 0);
  const safetyOverrideRateBaseline = Number(baseline.safety_override_rate_percent || 0);
  const safetyOverrideAvgActive = Number(selectedMetrics.safety_override_avg_fraction_active || 0) * 100;
  const story = buildEvaluationStory(baseline, selectedMetrics, context);
  const overrideDependence = getOverrideDependence(safetyOverrideRate);

  const metrics = [
    {
      label: 'Total Facility Reduction',
      value: `${totalSavingsPct.toFixed(2)}%`,
      icon: Zap,
      color: 'var(--accent)',
      desc: '',
    },
    {
      label: `PUE (${bestModelName})`,
      value: selectedMetrics.average_pue.toFixed(3),
      icon: Activity,
      color: 'var(--text)',
      desc: `Baseline: ${baseline.average_pue.toFixed(3)}`,
    },
    {
      label: 'Avg Temperature',
      value: `${selectedMetrics.average_temperature.toFixed(1)}°C`,
      icon: ThermometerSun,
      color: selectedMetrics.average_temperature > 55 ? 'var(--danger)' : 'var(--text)',
      desc: `Max: ${selectedMetrics.max_temperature.toFixed(1)}°C`,
    },
    {
      label: 'Safety Override',
      value: `${safetyOverrideRate.toFixed(1)}% steps`,
      icon: Shield,
      color: safetyOverrideRate > 10 ? 'var(--warning)' : 'var(--success)',
      desc: `Avg +${safetyOverrideAvgActive.toFixed(1)}% when active · Baseline ${safetyOverrideRateBaseline.toFixed(1)}%`,
    },
    {
      label: 'Safety Violations',
      value: selectedMetrics.safety_violations,
      icon: Shield,
      color: selectedMetrics.safety_violations === 0 ? 'var(--success)' : 'var(--danger)',
      desc: selectedMetrics.safety_violations === 0 ? 'Operating safely' : 'Thermal limits exceeded',
    },
  ];

  let decisionsList = results.metrics.decisions;
  let traceTitle = 'Decision Trace';
  if (decisionsList && !Array.isArray(decisionsList)) {
    let bestTraceModel = Object.keys(decisionsList)[0];
    if (results.metrics.models && Object.keys(results.metrics.models).length > 0) {
      const modelMetrics = results.metrics.models;
      bestTraceModel = Object.keys(modelMetrics).reduce((best, current) => (
        modelMetrics[current]?.total_power_consumption < modelMetrics[best]?.total_power_consumption ? current : best
      ));
    }
    decisionsList = decisionsList[bestTraceModel];
    traceTitle = `Decision Trace (${bestTraceModel})`;
  }

  return (
    <>
      {content}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginBottom: '32px' }}>
        <div className="card story-banner animate-fade-in">
          <div>
            <div className="card-title" style={{ marginBottom: '10px' }}>
              <CheckCircle2 size={12} />
              Result Story
            </div>
            <h2 style={{ fontSize: '20px', marginBottom: '6px', color: story.tone }}>{story.headline}</h2>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>{story.kicker}</p>
          </div>
          <div className="story-badges">
            <span className="badge badge-accent">{getScenarioLabel(context)}</span>
            <span className="badge">{formatCoolingMode(context.cooling_mode)} cooling</span>
            <span className={`badge ${selectedMetrics.safety_violations === 0 ? 'badge-success' : 'badge-warning'}`}>
              {selectedMetrics.safety_violations === 0 ? 'Thermally safe' : 'Safety reviewed'}
            </span>
            <span className="badge" style={{ color: overrideDependence.tone, borderColor: overrideDependence.tone }}>
              Override {overrideDependence.label}
            </span>
          </div>
        </div>

        <div className="evaluation-context-grid">
          {[
            ['Model', context.model],
            ['Config', formatConfigLabel(context.config)],
            ['Mode', formatCoolingMode(context.cooling_mode)],
            ['Baseline', context.baseline],
            ['Seed', context.seed ?? 'N/A'],
            ['Steps', Number(context.steps || 0).toLocaleString()],
          ].map(([label, value]) => (
            <div key={label} className="metric-card">
              <div className="text-label">{label}</div>
              <div className="metric-value" style={{ fontSize: '18px', marginTop: '6px' }}>{value}</div>
            </div>
          ))}
        </div>

        <div className="evaluation-downloads">
          <button
            className="btn btn-outline btn-sm"
            onClick={() => downloadFileFromApi(results.downloads.metrics_json, `${context.model || 'scari'}_metrics.json`, addToast)}
          >
            <Download size={12} />
            Metrics JSON
          </button>
          <button className="btn btn-outline btn-sm" onClick={downloadAllCharts}>
            <Image size={12} />
            All Charts
          </button>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px' }}>
          {metrics.map((metric, index) => (
            <div key={metric.label} className="metric-card animate-fade-in" style={{ animationDelay: `${index * 0.06}s` }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '7px', marginBottom: '10px' }}>
                <metric.icon size={14} color={metric.color} />
                <span className="text-label">{metric.label}</span>
              </div>
              <div className="metric-value" style={{ fontSize: '24px', color: metric.color, marginBottom: '4px' }}>
                {metric.value}
              </div>
              {metric.desc ? (
                <p style={{ fontSize: '11px', color: 'var(--muted)', lineHeight: 1.3 }}>{metric.desc}</p>
              ) : null}
            </div>
          ))}
          <div className="metric-card animate-fade-in" style={{ gridColumn: '1 / -1', border: '1px dashed var(--border)' }}>
            <div style={{ display: 'flex', gap: '10px', alignItems: 'flex-start' }}>
              <AlertCircle size={14} style={{ marginTop: '2px', color: 'var(--muted)', flexShrink: 0 }} />
              <p style={{ fontSize: '11px', color: 'var(--muted)', fontStyle: 'italic', margin: 0 }}>
                <strong>Reading tip:</strong> judge the run by savings, safety and safety-override dependence together, not by a single KPI in isolation.
              </p>
            </div>
          </div>
        </div>
      </div>

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
          {results.images.map((imagePath, index) => {
            const label = getChartLabel(imagePath);
            return (
              <div key={imagePath} className="card-chart animate-fade-in" style={{ animationDelay: `${index * 0.05}s` }}>
                <div className="chart-header">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div>
                      <div className="chart-title">{label.title}</div>
                      <div className="chart-desc">{label.desc}</div>
                    </div>
                    <button
                      className="btn btn-ghost btn-sm"
                      onClick={() => downloadChart(imagePath, `scari_${label.title.toLowerCase().replace(/\s/g, '_')}.png`)}
                      title="Download chart"
                      style={{ marginLeft: '8px', flexShrink: 0 }}
                    >
                      <Download size={13} />
                    </button>
                  </div>
                </div>
                <img
                  src={buildApiUrl(imagePath)}
                  alt={label.title}
                  className="chart-img"
                  draggable={false}
                />
              </div>
            );
          })}
        </div>
      </div>

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
              <span className="text-label">CO2 Offset (Yearly)</span>
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

      {Array.isArray(decisionsList) && decisionsList.length > 0 && (
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
                {decisionsList.map((decision) => (
                  <div
                    key={decision.step}
                    className={`decision-item ${selectedDecision?.step === decision.step ? 'active' : ''}`}
                    onClick={() => setSelectedDecision(decision)}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontWeight: 600, fontSize: '12px' }}>Step {decision.step}</span>
                      <span
                        style={{
                          fontSize: '11px',
                          fontWeight: 700,
                          fontFamily: 'var(--font-mono)',
                          color: decision.avg_temp > 60 ? 'var(--danger)' : decision.avg_temp > 50 ? 'var(--warning)' : 'var(--success)',
                        }}
                      >
                        {decision.avg_temp.toFixed(1)}°C
                      </span>
                    </div>
                    <div style={{ marginTop: '6px' }} className="progress-track">
                      <div
                        className="progress-fill"
                        style={{
                          width: `${decision.confidence * 100}%`,
                          background: selectedDecision?.step === decision.step ? 'var(--accent)' : 'var(--border-strong)',
                        }}
                      />
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
                      {selectedDecision.reasoning.map((reason) => (
                        <div key={reason} style={{ display: 'flex', gap: '10px', alignItems: 'flex-start' }}>
                          <ChevronRight size={12} color="var(--muted)" style={{ marginTop: '3px', flexShrink: 0 }} />
                          <p style={{ fontSize: '13px', lineHeight: 1.6, color: 'var(--text-secondary)' }}>{reason}</p>
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
                        {Object.entries(selectedDecision.feature_importance).map(([feature, value]) => (
                          <div key={feature}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '5px' }}>
                              <span style={{ color: 'var(--text-secondary)' }}>{feature}</span>
                              <span style={{ fontWeight: 700, fontFamily: 'var(--font-mono)' }}>{(value * 100).toFixed(1)}%</span>
                            </div>
                            <div className="progress-track" style={{ height: '5px' }}>
                              <div
                                className="progress-fill"
                                style={{
                                  width: `${Math.min(100, value * 100 * 3)}%`,
                                  background: 'var(--accent)',
                                  transition: 'width 0.4s ease',
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
                <div className="card" style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '200px' }}>
                  <p style={{ color: 'var(--muted)', fontSize: '13px' }}>Select a step to view control reasoning</p>
                </div>
              )}
            </div>
          </div>
        </section>
      )}
    </>
  );
};

export default AnalyticsView;
