import React from 'react';

const ModalOverlay = ({ children, theme }) => (
  <div
    style={{
      position: 'fixed',
      inset: 0,
      background: theme === 'dark' ? 'rgba(0,0,0,0.7)' : 'rgba(0,0,0,0.3)',
      backdropFilter: 'blur(4px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
    }}
  >
    {children}
  </div>
);

export default ModalOverlay;
