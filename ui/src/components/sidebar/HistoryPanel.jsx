import React from 'react';
import { History, RefreshCw, Trash2 } from 'lucide-react';

import { getSavingsBasisLabel } from '../../appUtils';

const HistoryPanel = ({
  evalHistory,
  loadingEvalHistory,
  onDeleteEvalResult,
  onFetchEvalHistory,
  onLoadEvalResult,
}) => (
  <section className="sidebar-section sidebar-history-section">
    <div className="card-title" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
      <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
        <History size={11} />
        Eval History
      </span>
      <button className="btn btn-ghost" onClick={onFetchEvalHistory} style={{ padding: '3px' }}>
        <RefreshCw size={11} className={loadingEvalHistory ? 'spin' : ''} />
      </button>
    </div>
    <div style={{ overflowY: 'auto', flex: 1, marginTop: '4px' }}>
      {evalHistory.length === 0 && !loadingEvalHistory && (
        <p style={{ fontSize: '12px', color: 'var(--muted)', fontStyle: 'italic', padding: '16px 0', textAlign: 'center' }}>
          No history found
        </p>
      )}
      {evalHistory.map((entry) => (
        <div
          key={entry.id}
          className="group"
          onClick={() => onLoadEvalResult(entry.id)}
          style={{ padding: '8px 10px', marginBottom: '4px' }}
        >
          <div style={{ flex: 1, minWidth: 0 }}>
            <p style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {entry.id.split('_').slice(0, -2).join('_') || 'Evaluation'}
            </p>
            <p style={{ fontSize: '10px', color: 'var(--muted)', marginTop: '2px' }}>
              {entry.timestamp} · {entry.savings?.toFixed(1)}% {getSavingsBasisLabel(entry.savings_basis)}
            </p>
          </div>
          <button
            className="btn btn-ghost btn-sm"
            onClick={(event) => onDeleteEvalResult(entry.id, event)}
            style={{ padding: '3px', color: 'var(--danger)', marginLeft: '8px' }}
          >
            <Trash2 size={11} />
          </button>
        </div>
      ))}
    </div>
  </section>
);

export default HistoryPanel;
