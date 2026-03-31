import React from 'react';
import { AlertCircle, CheckCircle2 } from 'lucide-react';

const Toast = ({ message, type }) => (
  <div className={`toast animate-slide-up ${type}`}>
    {type === 'success'
      ? <CheckCircle2 size={15} color="var(--success)" />
      : <AlertCircle size={15} color="var(--danger)" />}
    <span>{message}</span>
  </div>
);

export default Toast;
