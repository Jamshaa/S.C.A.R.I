import React from 'react';
import { Moon, Sun } from 'lucide-react';

const SidebarHeader = ({ theme, onToggleTheme }) => (
  <div className="sidebar-section" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
    <div>
      <h1 style={{ letterSpacing: '-0.05em', fontSize: '24px' }}>S.C.A.R.I</h1>
      <p
        style={{
          fontSize: '9px',
          textTransform: 'uppercase',
          letterSpacing: '0.18em',
          fontWeight: 700,
          color: 'var(--muted)',
          marginTop: '3px',
        }}
      >
        Cooling Intelligence
      </p>
    </div>
    <button
      className="btn btn-ghost"
      onClick={onToggleTheme}
      title={theme === 'dark' ? 'Light mode' : 'Dark mode'}
    >
      {theme === 'dark' ? <Sun size={15} /> : <Moon size={15} />}
    </button>
  </div>
);

export default SidebarHeader;
