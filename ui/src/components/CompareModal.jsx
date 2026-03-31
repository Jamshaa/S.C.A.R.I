import React from 'react';
import { GitMerge } from 'lucide-react';

const CompareModal = ({
  compareSelections,
  models,
  onCancel,
  onConfirm,
  onSelectionsChange,
  open,
}) => {
  if (!open) {
    return null;
  }

  return (
    <div className="modal-overlay">
      <div className="modal-content animate-slide-up" style={{ width: '400px' }}>
        <div className="modal-header">
          <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <GitMerge size={16} color="var(--accent)" />
            Multi-Model Comparison
          </h3>
        </div>
        <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '8px' }}>
            Select exactly one model of each cooling type to compare their efficiency and thermal safety.
          </p>
          <div className="form-group" style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <label style={{ color: 'var(--text)', fontSize: '11px', fontWeight: 600, textTransform: 'uppercase' }}>1. Air Cooling Model</label>
            <select
              style={{ width: '100%', padding: '8px', borderRadius: '6px', background: 'var(--surface)', color: 'var(--text)', border: '1px solid var(--border)' }}
              value={compareSelections.air}
              onChange={(event) => onSelectionsChange((previous) => ({ ...previous, air: event.target.value }))}
            >
              <option value="">-- Select Air Model --</option>
              {models.map((model) => (
                <option key={`air-${model}`} value={model}>{model}</option>
              ))}
            </select>
          </div>
          <div className="form-group" style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <label style={{ color: 'var(--text)', fontSize: '11px', fontWeight: 600, textTransform: 'uppercase' }}>2. Liquid Cooling Model</label>
            <select
              style={{ width: '100%', padding: '8px', borderRadius: '6px', background: 'var(--surface)', color: 'var(--text)', border: '1px solid var(--border)' }}
              value={compareSelections.liquid}
              onChange={(event) => onSelectionsChange((previous) => ({ ...previous, liquid: event.target.value }))}
            >
              <option value="">-- Select Liquid Model --</option>
              {models.map((model) => (
                <option key={`liq-${model}`} value={model}>{model}</option>
              ))}
            </select>
          </div>
          <div className="form-group" style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <label style={{ color: 'var(--text)', fontSize: '11px', fontWeight: 600, textTransform: 'uppercase' }}>3. Hybrid Cooling Model</label>
            <select
              style={{ width: '100%', padding: '8px', borderRadius: '6px', background: 'var(--surface)', color: 'var(--text)', border: '1px solid var(--border)' }}
              value={compareSelections.hybrid}
              onChange={(event) => onSelectionsChange((previous) => ({ ...previous, hybrid: event.target.value }))}
            >
              <option value="">-- Select Hybrid Model --</option>
              {models.map((model) => (
                <option key={`hyb-${model}`} value={model}>{model}</option>
              ))}
            </select>
          </div>
        </div>
        <div className="modal-footer" style={{ borderTop: '1px solid var(--border)', padding: '16px', marginTop: '16px', display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
          <button className="btn btn-outline" onClick={onCancel}>Cancel</button>
          <button
            className="btn btn-primary"
            onClick={onConfirm}
            disabled={!compareSelections.air || !compareSelections.liquid || !compareSelections.hybrid}
          >
            Start Comparison
          </button>
        </div>
      </div>
    </div>
  );
};

export default CompareModal;
