import React, { useCallback, useEffect, useRef, useState } from 'react';
import { AlertCircle, BarChart3, ChevronRight, Globe, Leaf } from 'lucide-react';

import DataCenterCalculator from './DataCenterCalculator';
import GlobalEmissions from './GlobalEmissions';
import { getTrainingConfigForMode } from './config';
import { apiFetch, apiJsonFetch, jsonRequest } from './apiClient';
import { downloadFileFromApi, fetchWithRetry } from './appUtils';
import CompareModal from './components/CompareModal';
import ModalOverlay from './components/ModalOverlay';
import Toast from './components/Toast';
import HistoryPanel from './components/sidebar/HistoryPanel';
import RegistryPanel from './components/sidebar/RegistryPanel';

import SidebarHeader from './components/sidebar/SidebarHeader';
import TrainingPanel from './components/sidebar/TrainingPanel';
import AnalyticsView from './views/AnalyticsView';
import WorkflowView from './views/WorkflowView';

const TAB_COPY = {
  workflow: {
    title: 'Workflow',
    subtitle: 'Choose model, run evaluation, read results, project impact',
  },
  analytics: {
    title: 'Evaluation',
    subtitle: 'Model evaluation and performance',
  },
  calculator: {
    title: 'Sustainability',
    subtitle: 'Resource efficiency and ROI analysis',
  },
  global: {
    title: 'Global Emissions',
    subtitle: 'Worldwide energy and CO2 intelligence',
  },
};

const App = () => {
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState('');
  const [isTraining, setIsTraining] = useState(false);
  const [trainingSteps, setTrainingSteps] = useState(600000);
  const [trainingName, setTrainingName] = useState('scari_thermal_safe');
  const [coolingMode, setCoolingMode] = useState('AIR');
  const [trainingProgress, setTrainingProgress] = useState(0);
  const [lastLog, setLastLog] = useState('');
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [evalSteps, setEvalSteps] = useState(5000);
  const [evalName, setEvalName] = useState('eval_optimization');
  const [evalLog, setEvalLog] = useState('');
  const [results, setResults] = useState(null);
  const [evalHistory, setEvalHistory] = useState([]);
  const [loadingEvalHistory, setLoadingEvalHistory] = useState(false);
  const [selectedDecision, setSelectedDecision] = useState(null);
  const [isRenaming, setIsRenaming] = useState(false);
  const [renameTarget, setRenameTarget] = useState('');
  const [newName, setNewName] = useState('');
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState('');
  const [toasts, setToasts] = useState([]);
  const [isCompareModalOpen, setIsCompareModalOpen] = useState(false);
  const [compareSelections, setCompareSelections] = useState({ air: '', liquid: '', hybrid: '' });
  const [theme, setTheme] = useState(() => (
    window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  ));
  const [mainTab, setMainTab] = useState('workflow');

  const isTrainingRef = useRef(isTraining);
  const isEvaluatingRef = useRef(isEvaluating);

  useEffect(() => {
    isTrainingRef.current = isTraining;
  }, [isTraining]);

  useEffect(() => {
    isEvaluatingRef.current = isEvaluating;
  }, [isEvaluating]);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  const addToast = useCallback((message, type = 'success') => {
    const id = Date.now();
    setToasts((previous) => [...previous, { id, message, type }]);
    setTimeout(() => {
      setToasts((previous) => previous.filter((toast) => toast.id !== id));
    }, 3500);
  }, []);

  const clearResults = useCallback(() => {
    setResults(null);
    setSelectedDecision(null);
  }, []);

  const fetchModels = useCallback(async () => {
    try {
      const data = await apiJsonFetch('/models');
      setModels(data.models || []);
    } catch (error) {
      addToast(`Failed to fetch models: ${error.message}`, 'error');
    }
  }, [addToast]);

  const fetchEvalHistory = useCallback(async () => {
    setLoadingEvalHistory(true);
    try {
      const data = await apiJsonFetch('/history');
      setEvalHistory(data.history || []);
    } catch (error) {
      addToast(`Failed to fetch evaluation history: ${error.message}`, 'error');
    } finally {
      setLoadingEvalHistory(false);
    }
  }, [addToast]);

  const fetchResults = useCallback(async () => {
    try {
      const response = await fetchWithRetry('/evaluation-results');
      if (!response) {
        return;
      }
      const data = await response.json();
      if (data.metrics) {
        setResults(data);
      }
    } catch (error) {
      console.debug('Failed to fetch latest evaluation results', error);
    }
  }, []);

  const fetchStatus = useCallback(async () => {
    try {
      const [statusResponse, evaluationResponse] = await Promise.all([
        fetchWithRetry('/status'),
        fetchWithRetry('/evaluation-status'),
      ]);

      if (statusResponse) {
        const statusData = await statusResponse.json();
        if (statusData.is_training) {
          setIsTraining(true);
          setTrainingProgress(statusData.progress || 0);
          setLastLog(statusData.last_log || '');
        } else if (isTrainingRef.current) {
          setIsTraining(false);
          setTrainingProgress(0);
          fetchModels();
        }
      }

      if (evaluationResponse) {
        const evaluationData = await evaluationResponse.json();
        if (evaluationData.is_evaluating) {
          setIsEvaluating(true);
          setEvalLog(evaluationData.last_log || '');
        } else if (isEvaluatingRef.current) {
          setIsEvaluating(false);
          setEvalLog('');
          fetchResults();
          fetchEvalHistory();
        }
      }
    } catch (error) {
      console.debug('Status polling failed', error);
    }
  }, [fetchEvalHistory, fetchModels, fetchResults]);

  useEffect(() => {
    fetchModels();
    fetchEvalHistory();

    let isMounted = true;
    let errorCount = 0;

    const poll = async () => {
      if (!isMounted) {
        return;
      }
      try {
        await fetchStatus();
        errorCount = 0;
      } catch (error) {
        errorCount += 1;
        console.debug('Polling iteration failed', error);
        if (errorCount > 5) {
          console.error('Polling stopped due to consecutive errors.');
          addToast('Connection to backend lost. Polling stopped.', 'error');
          return;
        }
      }
      if (isMounted) {
        const delay = Math.min(2000 * Math.pow(1.2, errorCount), 10000);
        setTimeout(poll, delay);
      }
    };

    const timeout = setTimeout(poll, 2000);
    return () => {
      isMounted = false;
      clearTimeout(timeout);
    };
  }, [addToast, fetchEvalHistory, fetchModels, fetchStatus]);

  const loadEvalResult = async (runId) => {
    try {
      const data = await apiJsonFetch(`/history/${runId}`);
      setResults(data);
      setSelectedDecision(null);
      addToast(`Loaded evaluation: ${runId}`, 'success');
      setMainTab('analytics');
    } catch (error) {
      addToast(`Failed to load: ${error.message}`, 'error');
    }
  };

  const deleteEvalResult = async (runId, event) => {
    if (event) {
      event.stopPropagation();
    }
    if (!window.confirm(`Delete evaluation ${runId}?`)) {
      return;
    }
    try {
      await apiFetch(`/history/${runId}`, { method: 'DELETE' });
      setEvalHistory((previous) => previous.filter((entry) => entry.id !== runId));
      addToast('Evaluation deleted', 'success');
    } catch (error) {
      addToast(`Delete failed: ${error.message}`, 'error');
    }
  };

  const handleTrain = async () => {
    try {
      await apiFetch('/train', jsonRequest('POST', {
        timesteps: trainingSteps,
        name: trainingName,
        config: getTrainingConfigForMode(coolingMode),
        cooling_mode: coolingMode,
      }));
      setIsTraining(true);
      setTrainingProgress(0);
      addToast(`Training started (${coolingMode} cooling)`);
    } catch (error) {
      addToast(error.message || 'Training failed', 'error');
    }
  };

  const handleRunComparison = async () => {
    const { air, liquid, hybrid } = compareSelections;
    if (!air || !liquid || !hybrid) {
      addToast('Please select all three models for comparison', 'error');
      return;
    }
    setIsCompareModalOpen(false);
    setIsEvaluating(true);
    setEvalLog('Requesting comparative evaluation...');
    try {
      await apiFetch('/evaluate', jsonRequest('POST', {
        model: 'MULTI',
        models: [air, liquid, hybrid],
        steps: evalSteps,
        name: evalName,
      }));
      addToast(`Comparing: ${air}, ${liquid}, ${hybrid}`);
    } catch (error) {
      addToast(error.message || 'Evaluation failed', 'error');
      setIsEvaluating(false);
    }
  };

  const handleEvaluate = async () => {
    if (!selectedModel) {
      addToast('Select a model first', 'error');
      return;
    }
    setIsEvaluating(true);
    setEvalLog('Requesting evaluation...');
    try {
      await apiFetch('/evaluate', jsonRequest('POST', {
        model: selectedModel,
        steps: evalSteps,
        name: evalName,
      }));
      setEvalLog('');
      addToast(`Evaluating ${selectedModel}`);
    } catch (error) {
      addToast(error.message || 'Evaluation failed', 'error');
    }
  };

  const handleRename = async () => {
    if (!newName.trim()) {
      return;
    }
    try {
      await apiFetch('/models/rename', jsonRequest('POST', { old_name: renameTarget, new_name: newName }));
      addToast('Model renamed', 'success');
      const finalName = newName.endsWith('.zip') ? newName : `${newName}.zip`;
      setModels((previous) => previous.map((model) => (model === renameTarget ? finalName : model)));
      if (selectedModel === renameTarget) {
        setSelectedModel(finalName);
      }
      setIsRenaming(false);
      setNewName('');
    } catch (error) {
      addToast(error.message || 'Rename failed', 'error');
    }
  };

  const handleRequestDelete = (modelName, event) => {
    event.stopPropagation();
    setDeleteTarget(modelName);
    setIsDeleting(true);
  };

  const handleRequestDeleteAll = () => {
    setDeleteTarget('ALL');
    setIsDeleting(true);
  };

  const confirmDelete = async () => {
    if (!deleteTarget) {
      return;
    }

    if (deleteTarget === 'ALL') {
      try {
        const data = await apiJsonFetch('/models', { method: 'DELETE' });
        addToast(data.message || 'All models deleted', 'success');
        setModels([]);
        setSelectedModel('');
      } catch (error) {
        addToast(`Failed to delete all models: ${error.message}`, 'error');
      }
    } else {
      try {
        await apiFetch(`/models/${deleteTarget}`, { method: 'DELETE' });
        addToast(`Deleted ${deleteTarget}`, 'success');
        setModels((previous) => previous.filter((model) => model !== deleteTarget));
        if (selectedModel === deleteTarget) {
          setSelectedModel('');
        }
      } catch (error) {
        addToast(`Failed to delete model: ${error.message}`, 'error');
      }
    }

    setIsDeleting(false);
    setDeleteTarget('');
  };

  const downloadChart = async (imageUrl, filename) => {
    await downloadFileFromApi(imageUrl, filename, addToast);
  };

  const downloadAllCharts = async () => {
    if (!results?.images) {
      return;
    }
    for (let index = 0; index < results.images.length; index += 1) {
      await downloadChart(results.images[index], `scari_chart_${index + 1}.png`);
    }
  };

  const toggleTheme = () => {
    setTheme((previous) => (previous === 'dark' ? 'light' : 'dark'));
  };

  const activeTabCopy = TAB_COPY[mainTab] || TAB_COPY.workflow;

  return (
    <div className="app-container">
      {isDeleting && (
        <ModalOverlay theme={theme}>
          <div
            className="card animate-fade-in"
            style={{
              width: '420px',
              padding: '28px',
              border: '1px solid var(--danger)',
              margin: 0,
              boxShadow: 'var(--shadow-lg)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px', color: 'var(--danger)' }}>
              <AlertCircle size={20} />
              <h3 style={{ textTransform: 'uppercase', letterSpacing: '0.05em' }}>Confirm Deletion</h3>
            </div>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '24px', lineHeight: 1.6 }}>
              {deleteTarget === 'ALL'
                ? 'Delete ALL models? This action cannot be undone.'
                : <span>Delete <strong style={{ color: 'var(--text)' }}>{deleteTarget}</strong>? This cannot be undone.</span>}
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

      {isRenaming && (
        <ModalOverlay theme={theme}>
          <div className="card animate-fade-in" style={{ width: '400px', padding: '28px', margin: 0, boxShadow: 'var(--shadow-lg)' }}>
            <h3 style={{ textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '3px' }}>
              Rename Model
            </h3>
            <p style={{ fontSize: '12px', color: 'var(--muted)', marginBottom: '16px' }}>{renameTarget}</p>
            <input
              value={newName}
              onChange={(event) => setNewName(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter') {
                  handleRename();
                }
              }}
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

      <aside className="sidebar">
        <SidebarHeader theme={theme} onToggleTheme={toggleTheme} />

        <TrainingPanel
          coolingMode={coolingMode}
          isTraining={isTraining}
          lastLog={lastLog}
          onCoolingModeChange={setCoolingMode}
          onTrain={handleTrain}
          setTrainingName={setTrainingName}
          setTrainingSteps={setTrainingSteps}
          trainingName={trainingName}
          trainingProgress={trainingProgress}
          trainingSteps={trainingSteps}
        />

        <RegistryPanel
          evalName={evalName}
          evalSteps={evalSteps}
          isEvaluating={isEvaluating}
          models={models}
          onDeleteAll={handleRequestDeleteAll}
          onEvaluate={handleEvaluate}
          onModelDelete={handleRequestDelete}
          onModelRename={(model) => {
            setRenameTarget(model);
            setIsRenaming(true);
            setNewName(model);
          }}
          onModelsRefresh={fetchModels}
          onOpenComparison={() => setIsCompareModalOpen(true)}
          selectedModel={selectedModel}
          setEvalName={setEvalName}
          setEvalSteps={setEvalSteps}
          setSelectedModel={setSelectedModel}
        />

        <HistoryPanel
          evalHistory={evalHistory}
          loadingEvalHistory={loadingEvalHistory}
          onDeleteEvalResult={deleteEvalResult}
          onFetchEvalHistory={fetchEvalHistory}
          onLoadEvalResult={loadEvalResult}
        />
      </aside>

      <main className="main-content">
        <div className="content-area">
          <header
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'flex-end',
              paddingBottom: '20px',
              marginBottom: '32px',
              borderBottom: '1px solid var(--border)',
            }}
          >
            <div>
              <h1 style={{ fontSize: '26px', letterSpacing: '-0.04em', marginBottom: '3px' }}>
                {activeTabCopy.title}
              </h1>
              <p style={{ color: 'var(--muted)', fontWeight: 600, fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
                {activeTabCopy.subtitle}
              </p>
            </div>
            <div className="tab-bar" style={{ marginBottom: 0 }}>
              <button
                className={`tab-btn ${mainTab === 'workflow' ? 'active' : ''}`}
                onClick={() => setMainTab('workflow')}
              >
                <ChevronRight size={12} style={{ display: 'inline', verticalAlign: '-2px', marginRight: '5px' }} />
                Workflow
              </button>
              <button
                className={`tab-btn ${mainTab === 'analytics' ? 'active' : ''}`}
                onClick={() => setMainTab('analytics')}
              >
                <BarChart3 size={12} style={{ display: 'inline', verticalAlign: '-2px', marginRight: '5px' }} />
                Evaluation
              </button>
              <button
                className={`tab-btn ${mainTab === 'global' ? 'active' : ''}`}
                onClick={() => setMainTab('global')}
              >
                <Globe size={12} style={{ display: 'inline', verticalAlign: '-2px', marginRight: '5px' }} />
                Global
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

          {mainTab === 'workflow' && (
            <WorkflowView
              handleEvaluate={handleEvaluate}
              isEvaluating={isEvaluating}
              models={models}
              results={results}
              selectedModel={selectedModel}
              setMainTab={setMainTab}
            />
          )}

          {mainTab === 'analytics' && (
            <AnalyticsView
              addToast={addToast}
              downloadAllCharts={downloadAllCharts}
              downloadChart={downloadChart}
              evalLog={evalLog}
              evalSteps={evalSteps}
              handleEvaluate={handleEvaluate}
              isEvaluating={isEvaluating}
              isTraining={isTraining}
              lastLog={lastLog}
              results={results}
              selectedDecision={selectedDecision}
              selectedModel={selectedModel}
              setResults={clearResults}
              setSelectedDecision={setSelectedDecision}
              trainingProgress={trainingProgress}
            />
          )}

          {mainTab === 'calculator' && (
            <DataCenterCalculator onToast={addToast} evalResults={results} />
          )}

          {mainTab === 'global' && (
            <GlobalEmissions />
          )}
        </div>
      </main>

      <CompareModal
        compareSelections={compareSelections}
        models={models}
        onCancel={() => setIsCompareModalOpen(false)}
        onConfirm={handleRunComparison}
        onSelectionsChange={setCompareSelections}
        open={isCompareModalOpen}
      />

      <div className="toast-container">
        {toasts.map((toast) => <Toast key={toast.id} {...toast} />)}
      </div>
    </div>
  );
};

export default App;
