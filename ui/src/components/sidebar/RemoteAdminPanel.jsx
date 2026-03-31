import React from 'react';
import { Globe, Shield } from 'lucide-react';

const RemoteAdminPanel = ({ adminKey, onAdminKeyChange }) => (
  <section className="sidebar-section">
    <div className="card-title">
      <Shield size={11} />
      Remote Admin
    </div>
    <label>Admin Key</label>
    <input
      type="password"
      value={adminKey}
      onChange={(event) => onAdminKeyChange(event.target.value)}
      placeholder="Optional for protected deployments"
      autoComplete="off"
    />
    <p style={{ fontSize: '11px', color: 'var(--muted)', lineHeight: 1.5, marginTop: '8px' }}>
      Stored in this browser session only. Localhost keeps working without it; remote train, evaluate and delete actions will send it as <code>X-API-Key</code>.
    </p>
    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '8px', color: 'var(--muted)', fontSize: '11px' }}>
      <Globe size={11} />
      <span>{adminKey ? 'Remote admin key ready' : 'No admin key loaded'}</span>
    </div>
  </section>
);

export default RemoteAdminPanel;
