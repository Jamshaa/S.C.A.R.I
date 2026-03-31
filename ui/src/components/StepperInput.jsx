import React, { useEffect, useRef, useState } from 'react';
import { Minus, Plus } from 'lucide-react';

import { fmtSteps } from '../appUtils';

const StepperInput = ({ value, onChange, step = 1000, min = 0, max = Infinity, presets = [] }) => {
  const intervalRef = useRef(null);
  const timeoutRef = useRef(null);
  const valueRef = useRef(value);
  const [inputValue, setInputValue] = useState(fmtSteps(value));

  const clamp = (nextValue) => Math.max(min, Math.min(max, nextValue));

  const stopHold = () => {
    clearTimeout(timeoutRef.current);
    clearInterval(intervalRef.current);
  };

  const startHoldSafe = (delta) => {
    onChange(clamp(value + delta));
    timeoutRef.current = setTimeout(() => {
      intervalRef.current = setInterval(() => {
        valueRef.current = clamp(valueRef.current + delta);
        onChange(valueRef.current);
      }, 80);
    }, 400);
  };

  useEffect(() => {
    valueRef.current = value;
  }, [value]);

  useEffect(() => {
    setInputValue(fmtSteps(value));
  }, [value]);

  const handleInputBlur = () => {
    const raw = inputValue.toLowerCase();
    let parsed = parseFloat(raw);
    if (raw.endsWith('m')) {
      parsed *= 1_000_000;
    } else if (raw.endsWith('k')) {
      parsed *= 1_000;
    }
    if (Number.isNaN(parsed)) {
      setInputValue(fmtSteps(value));
      return;
    }
    const clamped = clamp(parsed);
    onChange(clamped);
    setInputValue(fmtSteps(clamped));
  };

  return (
    <div>
      <div className="stepper">
        <button
          className="stepper-btn"
          onMouseDown={() => startHoldSafe(-step)}
          onMouseUp={stopHold}
          onMouseLeave={stopHold}
          tabIndex={-1}
        >
          <Minus size={14} />
        </button>
        <input
          type="text"
          className="stepper-input-field"
          value={inputValue}
          onChange={(event) => setInputValue(event.target.value)}
          onBlur={handleInputBlur}
          onKeyDown={(event) => {
            if (event.key === 'Enter') {
              handleInputBlur();
            }
          }}
        />
        <button
          className="stepper-btn"
          onMouseDown={() => startHoldSafe(step)}
          onMouseUp={stopHold}
          onMouseLeave={stopHold}
          tabIndex={-1}
        >
          <Plus size={14} />
        </button>
      </div>
      {presets.length > 0 && (
        <div className="preset-grid">
          {presets.map((preset) => (
            <button
              key={preset}
              className={`preset-pill ${value === preset ? 'active' : ''}`}
              onClick={() => onChange(preset)}
            >
              {fmtSteps(preset)}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default StepperInput;
