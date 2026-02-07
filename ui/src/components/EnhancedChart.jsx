import React from 'react';
import { LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ComposedChart } from 'recharts';

/**
 * Enhanced Chart Components with improved styling and thermal awareness
 */

export const ThermalChart = ({ data, maxThreshold = 60, criticalThreshold = 65 }) => {
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload[0]) {
      const data = payload[0].payload;
      return (
        <div style={{
          background: 'rgba(3, 4, 7, 0.9)',
          border: '1px solid rgba(0, 243, 255, 0.5)',
          borderRadius: '8px',
          padding: '0.75rem',
          backdropFilter: 'blur(10px)'
        }}>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-primary)', margin: 0 }}>
            <strong>Step {data.step}</strong>
          </p>
          <p style={{ fontSize: '0.8rem', color: '#00ff88', margin: '4px 0 0 0' }}>
            Temp: {data.temp.toFixed(1)}°C
          </p>
          <p style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', margin: '2px 0 0 0' }}>
            Status: {data.temp >= criticalThreshold ? '🔴 CRITICAL' : data.temp >= maxThreshold ? '🟡 WARNING' : '🟢 SAFE'}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <ResponsiveContainer width="100%" height={300}>
      <ComposedChart data={data} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
        <defs>
          <linearGradient id="tempGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="var(--accent-primary)" stopOpacity={0.8} />
            <stop offset="95%" stopColor="var(--accent-primary)" stopOpacity={0.2} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" vertical={false} />
        <XAxis dataKey="step" stroke="var(--text-secondary)" style={{ fontSize: '0.75rem' }} />
        <YAxis stroke="var(--text-secondary)" style={{ fontSize: '0.75rem' }} domain={[20, 70]} />
        
        {/* Safe Zone Background */}
        <Area 
          type="monotone" 
          dataKey={() => maxThreshold} 
          stroke="transparent" 
          fill="rgba(0, 255, 136, 0.05)" 
          isAnimationActive={false}
        />
        
        <Area
          type="monotone"
          dataKey="temp"
          fill="url(#tempGradient)"
          stroke="var(--accent-primary)"
          dot={false}
          strokeWidth={2}
        />
        
        {/* Temperature Reference Lines */}
        <Line 
          type="monotone" 
          dataKey={() => maxThreshold}
          stroke="var(--accent-warning)"
          strokeDasharray="5 5"
          dot={false}
          strokeWidth={1.5}
          name="Max Safe (60°C)"
          isAnimationActive={false}
        />
        
        <Tooltip content={<CustomTooltip />} />
        <Legend wrapperStyle={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }} />
      </ComposedChart>
    </ResponsiveContainer>
  );
};

export const EfficiencyChart = ({ data }) => {
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload[0]) {
      const data = payload[0].payload;
      const pue = data.total_power / (data.total_power - data.cooling_power);
      return (
        <div style={{
          background: 'rgba(3, 4, 7, 0.9)',
          border: '1px solid rgba(0, 100, 255, 0.5)',
          borderRadius: '8px',
          padding: '0.75rem',
          backdropFilter: 'blur(10px)'
        }}>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-primary)', margin: 0 }}>
            <strong>Step {data.step}</strong>
          </p>
          <p style={{ fontSize: '0.8rem', color: 'var(--accent-secondary)', margin: '4px 0 0 0' }}>
            Total Power: {data.total_power.toFixed(0)}W
          </p>
          <p style={{ fontSize: '0.8rem', color: 'var(--accent-success)', margin: '2px 0 0 0' }}>
            Cooling: {data.cooling_power.toFixed(0)}W
          </p>
          <p style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', margin: '2px 0 0 0' }}>
            PUE: {pue.toFixed(2)}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <ResponsiveContainer width="100%" height={300}>
      <ComposedChart data={data} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
        <defs>
          <linearGradient id="powerGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="var(--accent-secondary)" stopOpacity={0.8} />
            <stop offset="95%" stopColor="var(--accent-secondary)" stopOpacity={0.1} />
          </linearGradient>
          <linearGradient id="coolingGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="var(--accent-success)" stopOpacity={0.7} />
            <stop offset="95%" stopColor="var(--accent-success)" stopOpacity={0.1} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" vertical={false} />
        <XAxis dataKey="step" stroke="var(--text-secondary)" style={{ fontSize: '0.75rem' }} />
        <YAxis stroke="var(--text-secondary)" style={{ fontSize: '0.75rem' }} yAxisId="left" />
        
        <BarChart data={data}>
          <Bar 
            dataKey="total_power" 
            fill="url(#powerGradient)" 
            stroke="var(--accent-secondary)" 
            strokeWidth={1}
            yAxisId="left"
            radius={[4, 4, 0, 0]}
            name="Total Power"
          />
        </BarChart>
        
        <Line
          type="monotone"
          dataKey="cooling_power"
          stroke="var(--accent-success)"
          strokeWidth={2}
          dot={false}
          yAxisId="left"
          name="Cooling Power"
        />
        
        <Tooltip content={<CustomTooltip />} />
        <Legend wrapperStyle={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }} />
      </ComposedChart>
    </ResponsiveContainer>
  );
};

export const RewardChart = ({ data }) => {
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload[0]) {
      const data = payload[0].payload;
      return (
        <div style={{
          background: 'rgba(3, 4, 7, 0.9)',
          border: '1px solid rgba(176, 36, 255, 0.5)',
          borderRadius: '8px',
          padding: '0.75rem',
          backdropFilter: 'blur(10px)'
        }}>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-primary)', margin: 0 }}>
            <strong>Step {data.step}</strong>
          </p>
          <p style={{ fontSize: '0.8rem', color: 'var(--accent-purple)', margin: '4px 0 0 0' }}>
            Reward: {data.reward.toFixed(2)}
          </p>
          <p style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', margin: '2px 0 0 0' }}>
            Cumulative: {data.cumulative_reward.toFixed(0)}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <ResponsiveContainer width="100%" height={300}>
      <AreaChart data={data} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
        <defs>
          <linearGradient id="rewardGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="var(--accent-purple)" stopOpacity={0.8} />
            <stop offset="95%" stopColor="var(--accent-purple)" stopOpacity={0.1} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" vertical={false} />
        <XAxis dataKey="step" stroke="var(--text-secondary)" style={{ fontSize: '0.75rem' }} />
        <YAxis stroke="var(--text-secondary)" style={{ fontSize: '0.75rem' }} />
        
        <Area
          type="monotone"
          dataKey="cumulative_reward"
          fill="url(#rewardGradient)"
          stroke="var(--accent-purple)"
          dot={false}
          strokeWidth={2}
          name="Cumulative Reward"
        />
        
        <Tooltip content={<CustomTooltip />} />
        <Legend wrapperStyle={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }} />
      </AreaChart>
    </ResponsiveContainer>
  );
};

export const MetricsOverview = ({ metrics }) => {
  const getStatusColor = (value, type) => {
    if (type === 'temperature') {
      if (value >= 65) return 'var(--accent-danger)';
      if (value >= 60) return 'var(--accent-warning)';
      return 'var(--accent-success)';
    }
    return 'var(--accent-primary)';
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem' }}>
      {Object.entries(metrics).map(([key, value]) => (
        <div key={key} style={{
          background: 'var(--glass-bg)',
          border: '1px solid var(--glass-border)',
          borderRadius: '12px',
          padding: '1rem',
          textAlign: 'center'
        }}>
          <p style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '0.5rem', fontWeight: 700 }}>
            {key.replace(/_/g, ' ')}
          </p>
          <p style={{
            fontSize: '2rem',
            fontWeight: 800,
            color: getStatusColor(value, key)
          }}>
            {typeof value === 'number' ? (value < 1000 ? value.toFixed(1) : value.toFixed(0)) : value}
          </p>
        </div>
      ))}
    </div>
  );
};
